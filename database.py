# kucoin_app/database.py
# PostgreSQL database manager for trades, logs, and equity tracking

import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Load .env if available to allow configuring DATABASE_URL in env file
try:
    from dotenv import load_dotenv
    try:
        load_dotenv()
    except Exception:
        pass
except Exception:
    pass

# Enforce Postgres-only backend. DATABASE_URL must be set.
PG_CONN_INFO = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")

# Enforce Postgres-only backend. Fail fast if not configured.
if not PG_CONN_INFO:
    raise RuntimeError("DATABASE_URL is required; Postgres backend only. Set DATABASE_URL environment variable.")

try:
    import psycopg2
    import psycopg2.extras
except Exception as e:
    raise RuntimeError(f"psycopg2 is required but failed to import: {e}")

USE_PG = True

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent

class DatabaseManager:
    def get_learning_symbols(self) -> list:
        """Retorna todos os símbolos presentes em learning_stats."""
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT DISTINCT symbol FROM learning_stats ORDER BY symbol")
            rows = cur.fetchall()
            return [r[0] for r in rows if r[0]]
        except Exception as e:
            logger.error(f"Erro ao buscar símbolos de aprendizado: {e}")
            return []
        finally:
            conn.close()

    def get_learning_stats(self, symbol: str, param_name: str) -> list:
        """Retorna estatísticas de aprendizado para um símbolo e parâmetro."""
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT * FROM learning_stats
                WHERE symbol = ? AND param_name = ?
                ORDER BY param_value
                """,
                (symbol, param_name)
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Erro ao buscar learning_stats: {e}")
            return []
        finally:
            conn.close()

    def get_learning_history(self, symbol: str, param_name: str, limit: int = 2000) -> list:
        """Retorna histórico de aprendizado para um símbolo e parâmetro."""
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT * FROM learning_history
                WHERE symbol = ? AND param_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (symbol, param_name, limit)
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Erro ao buscar learning_history: {e}")
            return []
        finally:
            conn.close()

    def choose_bandit_param(self, symbol: str, param_name: str, candidates: list, epsilon: float = 0.1) -> float:
        """
        Escolhe um parâmetro usando estratégia epsilon-greedy baseada em histórico de recompensas.
        
        Args:
            symbol: Símbolo do ativo (ex: 'BTCUSDT')
            param_name: Nome do parâmetro (ex: 'take_profit_trailing_pct')
            candidates: Lista de valores candidatos para o parâmetro
            epsilon: Probabilidade de exploração (0.0 = sempre greedy, 1.0 = sempre random)
        
        Returns:
            Valor do parâmetro escolhido
        """
        import random
        
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            # Busca estatísticas atuais para os candidatos
            placeholders = ','.join(['?'] * len(candidates))
            cur.execute(f"""
                SELECT param_value, mean_reward, n
                FROM learning_stats
                WHERE symbol = ? AND param_name = ? AND param_value IN ({placeholders})
                ORDER BY mean_reward DESC
            """, [symbol, param_name] + candidates)
            
            stats = {row['param_value']: {'mean_reward': row['mean_reward'], 'n': row['n']} 
                    for row in cur.fetchall()}
            
            # Inicializa estatísticas para todos os candidatos (padrão: recompensa 0, n=0)
            candidate_stats = {}
            for candidate in candidates:
                if candidate in stats:
                    candidate_stats[candidate] = stats[candidate]
                else:
                    candidate_stats[candidate] = {'mean_reward': 0.0, 'n': 0}
            
            # Epsilon-greedy: exploração vs exploração
            if random.random() < epsilon:
                # Exploração: escolhe aleatoriamente
                return random.choice(candidates)
            else:
                # Greedy: escolhe o com maior recompensa média
                best_value = max(candidate_stats.keys(), key=lambda x: candidate_stats[x]['mean_reward'])
                return best_value
                
        except Exception as e:
            logger.error(f"Erro ao escolher parâmetro bandit: {e}")
            return random.choice(candidates)
        finally:
            conn.close()

    def update_bandit_reward(self, symbol: str, param_name: str, param_value: float, reward: float) -> bool:
        """
        Atualiza as recompensas do bandit learning após um trade.
        
        Args:
            symbol: Símbolo do ativo
            param_name: Nome do parâmetro
            param_value: Valor do parâmetro usado
            reward: Recompensa obtida (ex: profit_pct)
        
        Returns:
            True se atualizado com sucesso
        """
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            # Insere no histórico
            cur.execute("""
                INSERT INTO learning_history (symbol, param_name, param_value, reward, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (symbol, param_name, param_value, reward, time.time()))
            
            # Atualiza ou insere estatísticas
            cur.execute("""
                SELECT mean_reward, n FROM learning_stats
                WHERE symbol = ? AND param_name = ? AND param_value = ?
            """, (symbol, param_name, param_value))
            
            row = cur.fetchone()
            if row:
                # Atualiza média incremental
                old_mean = row['mean_reward']
                old_n = row['n']
                new_n = old_n + 1
                new_mean = ((old_mean * old_n) + reward) / new_n
                
                cur.execute("""
                    UPDATE learning_stats
                    SET mean_reward = ?, n = ?
                    WHERE symbol = ? AND param_name = ? AND param_value = ?
                """, (new_mean, new_n, symbol, param_name, param_value))
            else:
                # Insere novo registro
                cur.execute("""
                    INSERT INTO learning_stats (symbol, param_name, param_value, mean_reward, n)
                    VALUES (?, ?, ?, ?, ?)
                """, (symbol, param_name, param_value, reward, 1))
            
            conn.commit()
            logger.info(f"Bandit reward updated: {symbol} {param_name}={param_value} reward={reward}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar bandit reward: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    """Gerencia todas as operações do banco de dados"""

    def __init__(self):
        # Postgres DSN is in PG_CONN_INFO. If USE_PG is False we skip initialization
        # so the module can be imported in local/dev environments without a DB.
        self._enabled = USE_PG
        self._initialized = False
        if not self._enabled:
            return

        # Initialize database schema in background to avoid blocking UI startup.
        try:
            import threading
            threading.Thread(target=self._init_database_background, daemon=True).start()
        except Exception:
            # Fallback: try synchronously (rare)
            try:
                self.init_database()
                self._initialized = True
            except Exception:
                logger.exception("Erro ao inicializar o DB sincronamente")

    def _init_database_background(self):
        try:
            self.init_database()
            self._initialized = True
        except Exception:
            logger.exception("Erro na inicialização do DB em background")
    
    def get_connection(self):
        """Obtém uma conexão PostgreSQL. Retorna um objeto com .cursor(), .commit(), .close()."""
        if not USE_PG or psycopg2 is None:
            raise RuntimeError("DATABASE_URL não configurado; operação de banco indisponível em modo local.")
        # Use a short connect timeout so UI doesn't hang if DB is unreachable.
        try:
            conn = psycopg2.connect(PG_CONN_INFO, connect_timeout=2)
        except TypeError:
            # Some psycopg2 versions / DSN styles may not accept kwarg when DSN is passed as string.
            # Try to pass via environment variable fallback.
            conn = psycopg2.connect(PG_CONN_INFO)
        conn.autocommit = False
        class PGCursor:
            def __init__(self, cur):
                self._cur = cur
            def execute(self, sql, params=None):
                if params is None:
                    params = []
                if '%s' in sql:
                    sql2 = sql  # Já está no formato psycopg2
                else:
                    q_count = sql.count('?')
                    if q_count == len(params) and q_count > 0:
                        # Substitui cada '?' por '%s' individualmente
                        parts = sql.split('?')
                        sql2 = ''
                        for i, part in enumerate(parts[:-1]):
                            sql2 += part + '%s'
                        sql2 += parts[-1]
                    else:
                        sql2 = sql
                import logging
                logging.getLogger("autocoin_sql_debug").debug(f"SQL: {sql2} | params: {params}")
                return self._cur.execute(sql2, params)
            def executemany(self, sql, seq_of_params):
                seq_of_params = list(seq_of_params)
                n_params = len(seq_of_params[0]) if seq_of_params else 0
                if '%s' in sql:
                    sql2 = sql  # Já está no formato psycopg2
                else:
                    q_count = sql.count('?')
                    if q_count == n_params and q_count > 0:
                        parts = sql.split('?')
                        sql2 = ''
                        for i, part in enumerate(parts[:-1]):
                            sql2 += part + '%s'
                        sql2 += parts[-1]
                    else:
                        sql2 = sql
                import logging
                logging.getLogger("autocoin_sql_debug").debug(f"SQL: {sql2} | params: {seq_of_params}")
                return self._cur.executemany(sql2, seq_of_params)
            def fetchall(self):
                return self._cur.fetchall()
            def fetchone(self):
                return self._cur.fetchone()
            def close(self):
                try:
                    self._cur.close()
                except Exception:
                    pass
        class PGConnection:
            def __init__(self, conn):
                self._conn = conn
            def cursor(self):
                return PGCursor(self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor))
            def commit(self):
                return self._conn.commit()
            def rollback(self):
                return self._conn.rollback()
            def close(self):
                try:
                    return self._conn.close()
                except Exception:
                    pass
        return PGConnection(conn)
    
    def init_database(self):
        """Inicializa o esquema do banco de dados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela Trades
        def exec_sql(sql: str):
            # Executa DDL diretamente para PostgreSQL
            sql_pg = sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
            sql_pg = sql_pg.replace('DATETIME DEFAULT CURRENT_TIMESTAMP', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            sql_pg = sql_pg.replace('REAL', 'DOUBLE PRECISION')
            sql_pg = sql_pg.replace("\"", '"')
            try:
                cursor.execute(sql_pg)
            except Exception as e:
                logger.debug(f"Error executing PG DDL: {e} -- sql: {sql_pg}")

        exec_sql('''
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                timestamp REAL NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                price REAL NOT NULL,
                size REAL,
                funds REAL,
                profit REAL,
                commission REAL,
                order_id TEXT,
                bot_id TEXT,
                strategy TEXT,
                dry_run INTEGER DEFAULT 1,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela Bot sessions
        exec_sql('''
            CREATE TABLE IF NOT EXISTS bot_sessions (
                id TEXT PRIMARY KEY,
                pid INTEGER,
                symbol TEXT NOT NULL,
                mode TEXT NOT NULL,
                entry_price REAL NOT NULL,
                targets TEXT,
                trailing_stop_pct REAL,
                stop_loss_pct REAL,
                size REAL,
                funds REAL,
                start_ts REAL NOT NULL,
                end_ts REAL,
                status TEXT DEFAULT 'running',
                executed_parts TEXT,
                remaining_fraction REAL,
                total_profit REAL,
                dry_run INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela Equity snapshots (AGORA COM average_cost)
        exec_sql('''
            CREATE TABLE IF NOT EXISTS equity_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                balance_usdt REAL NOT NULL,
                btc_price REAL,
                average_cost REAL,  -- NOVO: Custo Médio Ponderado da Posição
                num_positions INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela Eternal Runs - histórico de ciclos do eternal mode
        exec_sql('''
            CREATE TABLE IF NOT EXISTS eternal_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id TEXT NOT NULL,
                run_number INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                profit_pct REAL,
                profit_usdt REAL,
                targets_hit INTEGER DEFAULT 0,
                total_targets INTEGER DEFAULT 0,
                start_ts REAL NOT NULL,
                end_ts REAL,
                status TEXT DEFAULT 'running',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela Bot logs
        exec_sql('''
            CREATE TABLE IF NOT EXISTS bot_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela Risk metrics
        exec_sql('''
            CREATE TABLE IF NOT EXISTS risk_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                symbol TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela Learning stats (estatísticas de aprendizado por parâmetro)
        exec_sql('''
            CREATE TABLE IF NOT EXISTS learning_stats (
                symbol TEXT NOT NULL,
                param_name TEXT NOT NULL,
                param_value REAL NOT NULL,
                mean_reward REAL NOT NULL,
                n INTEGER NOT NULL,
                PRIMARY KEY (symbol, param_name, param_value)
            )
        ''')
        
        # Tabela Learning history (histórico de recompensas)
        exec_sql('''
            CREATE TABLE IF NOT EXISTS learning_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                param_name TEXT NOT NULL,
                param_value REAL NOT NULL,
                reward REAL NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')
        
        # Cria índices
        for idx_sql in [
            'CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)',
            'CREATE INDEX IF NOT EXISTS idx_bot_sessions_status ON bot_sessions(status)',
            'CREATE INDEX IF NOT EXISTS idx_bot_logs_bot_id ON bot_logs(bot_id)',
            'CREATE INDEX IF NOT EXISTS idx_equity_timestamp ON equity_snapshots(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_learning_history_symbol_param ON learning_history(symbol, param_name)',
            'CREATE INDEX IF NOT EXISTS idx_learning_history_timestamp ON learning_history(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_learning_stats_symbol_param ON learning_stats(symbol, param_name)'
        ]:
            try:
                if USE_PG:
                    # Postgres will accept these index creations; ignore failures
                    cursor.execute(idx_sql)
                else:
                    cursor.execute(idx_sql)
            except Exception:
                try:
                    pass
                except Exception:
                    pass

        try:
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass
        logger.info("Database initialized successfully")
    
    def get_bot_ids(self):
        """
        Retorna lista de bot_id existentes em equity_snapshots.
        """
        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT DISTINCT bot_id
            FROM equity_snapshots
            WHERE bot_id IS NOT NULL
            ORDER BY bot_id
        """)

        rows = cur.fetchall()
        conn.close()

        return [r[0] for r in rows]


    # --- TRADES ---
    
    def insert_trade(self, trade_data: Dict[str, Any]) -> bool:
        """Insere um novo trade"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trades (
                    id, timestamp, symbol, side, price, size, funds,
                    profit, commission, order_id, bot_id, strategy,
                    dry_run, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_data.get('id'),
                trade_data.get('timestamp', time.time()),
                trade_data.get('symbol'),
                trade_data.get('side'),
                trade_data.get('price'),
                trade_data.get('size'),
                trade_data.get('funds'),
                trade_data.get('profit'),
                trade_data.get('commission'),
                trade_data.get('order_id'),
                trade_data.get('bot_id'),
                trade_data.get('strategy'),
                1 if trade_data.get('dry_run') else 0,
                json.dumps(trade_data.get('metadata', {}))
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Trade inserted: {trade_data.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Error inserting trade: {e}")
            return False
    
    def get_trades(self, bot_id: str = None):
        """
        Retorna trades, opcionalmente filtrados por bot_id.
        """
        conn = self.get_connection()
        cur = conn.cursor()

        if bot_id:
            cur.execute(
                """
                SELECT timestamp, profit, bot_id
                FROM trades
                WHERE bot_id = ?
                ORDER BY timestamp
                """,
                (bot_id,)
            )
        else:
            cur.execute(
                """
                SELECT timestamp, profit, bot_id
                FROM trades
                ORDER BY timestamp
                """
            )

        rows = cur.fetchall()
        conn.close()

        # Converte para lista de dicts (contrato com ChartsManager)
        return [
            {
                "timestamp": r[0],
                "profit": r[1],
                "bot_id": r[2],
            }
            for r in rows
        ]

    def get_trade_history_grouped(self, limit: int = 1000, bot_id: str = None, 
                                 only_real: bool = False, group_by_order_id: bool = True):
        """
        Retorna histórico de trades com opções de filtro e agrupamento.
        
        Args:
            limit: Número máximo de registros
            bot_id: Filtrar por bot específico
            only_real: Apenas trades reais (não dry-run)
            group_by_order_id: Agrupar por order_id para deduplicar
            
        Returns:
            Lista de dicionários com dados dos trades
        """
        conn = self.get_connection()
        cur = conn.cursor()
        
        query = """
            SELECT id, timestamp, symbol, side, price, size, funds, profit, 
                   commission, order_id, bot_id, strategy, dry_run, metadata
            FROM trades
            WHERE 1=1
        """
        params = []
        
        if bot_id:
            query += " AND bot_id = ?"
            params.append(bot_id)
            
        if only_real:
            query += " AND dry_run = 0"
        
        if group_by_order_id:
            query += " GROUP BY id, timestamp, symbol, side, price, size, funds, profit, commission, order_id, bot_id, strategy, dry_run, metadata"
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        # Converte para lista de dicts
        return [
            dict(r) if hasattr(r, 'keys') else {
                "id": r[0],
                "timestamp": r[1],
                "symbol": r[2],
                "side": r[3],
                "price": r[4],
                "size": r[5],
                "funds": r[6],
                "profit": r[7],
                "commission": r[8],
                "order_id": r[9],
                "bot_id": r[10],
                "strategy": r[11],
                "dry_run": r[12],
                "metadata": r[13],
            }
            for r in rows
        ]

    
    # --- BOT SESSIONS ---
    
    def insert_bot_session(self, session_data: Dict[str, Any]) -> bool:
        """Insere uma nova sessão do bot"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO bot_sessions (
                    id, pid, symbol, mode, entry_price, targets,
                    trailing_stop_pct, stop_loss_pct, size, funds,
                    start_ts, status, executed_parts, remaining_fraction,
                    dry_run
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_data.get('id'),
                session_data.get('pid'),
                session_data.get('symbol'),
                session_data.get('mode'),
                session_data.get('entry_price'),
                json.dumps(session_data.get('targets', [])),
                session_data.get('trailing_stop_pct'),
                session_data.get('stop_loss_pct'),
                session_data.get('size'),
                session_data.get('funds'),
                session_data.get('start_ts', time.time()),
                'running',
                json.dumps([]),
                session_data.get('remaining_fraction', 1.0),
                1 if session_data.get('dry_run') else 0
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Bot session created: {session_data.get('id')} (PID: {session_data.get('pid')})")
            return True
        except Exception as e:
            logger.error(f"Error inserting bot session: {e}")
            return False
    
    def update_bot_session(self, bot_id: str, updates: Dict[str, Any]) -> bool:
        """Atualiza a sessão do bot"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [bot_id]
            
            cursor.execute(f"UPDATE bot_sessions SET {set_clause} WHERE id = ?", values)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating bot session: {e}")
            return False
    
    def get_active_bots(self) -> List[Dict]:
        """Obtém todas as sessões ativas do bot"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bot_sessions WHERE status = 'running'")
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting active bots: {e}")
            return []
    
    # --- EQUITY SNAPSHOTS ---
    
    def add_equity_snapshot(self, balance_usdt: float, btc_price: float = None,
                           average_cost: float = None, num_positions: int = 0) -> bool:
        """Adiciona um snapshot de patrimônio (equity)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO equity_snapshots (timestamp, balance_usdt, btc_price, average_cost, num_positions)
                VALUES (?, ?, ?, ?, ?)
            ''', (time.time(), balance_usdt, btc_price, average_cost, num_positions))
            
            conn.commit()
            conn.close()
            logger.info(f"Equity snapshot added: ${balance_usdt:,.2f}")
            return True
        except Exception as e:
            logger.error(f"Error adding equity snapshot: {e}")
            return False
    
    def get_equity_history(self, days: int = 30) -> List[Dict]:
        """Obtém o histórico de patrimônio"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            start_ts = time.time() - (days * 86400)
            cursor.execute('''
                SELECT * FROM equity_snapshots 
                WHERE timestamp >= ? 
                ORDER BY timestamp ASC
            ''', (start_ts,))
            
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting equity history: {e}")
            return []
    
    # --- BOT LOGS ---
    
    def add_bot_log(self, bot_id: str, level: str, message: str, 
                    data: Dict = None) -> bool:
        """Adiciona uma entrada de log do bot"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO bot_logs (bot_id, timestamp, level, message, data)
                VALUES (?, ?, ?, ?, ?)
            ''', (bot_id, time.time(), level, message, 
                  json.dumps(data) if data else None))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding bot log: {e}")
            return False
    

    def get_bot_logs(self, bot_id: str, limit: int = 30) -> List[Dict]:
        """Obtém os últimos N logs do bot em ordem decrescente (mais recentes primeiro)"""
        try:
            limit = max(1, min(int(limit), 30))
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # ORDER BY timestamp DESC para retornar os mais recentes primeiro
            cursor.execute('''
                SELECT * FROM bot_logs 
                WHERE bot_id = ? 
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (bot_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting bot logs: {e}")
            return []
    
    # --- ETERNAL RUNS ---
    
    def add_eternal_run(self, bot_id: str, run_number: int, symbol: str,
                        entry_price: float, total_targets: int) -> int:
        """Inicia um novo ciclo do eternal mode"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO eternal_runs 
                (bot_id, run_number, symbol, entry_price, total_targets, start_ts, status)
                VALUES (?, ?, ?, ?, ?, ?, 'running')
            ''', (bot_id, run_number, symbol, entry_price, total_targets, time.time()))
            
            run_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return run_id
        except Exception as e:
            logger.error(f"Error adding eternal run: {e}")
            return -1
    
    def complete_eternal_run(self, run_id: int, exit_price: float, 
                             profit_pct: float, profit_usdt: float,
                             targets_hit: int) -> bool:
        """Finaliza um ciclo do eternal mode"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE eternal_runs 
                SET exit_price = ?, profit_pct = ?, profit_usdt = ?,
                    targets_hit = ?, end_ts = ?, status = 'completed'
                WHERE id = ?
            ''', (exit_price, profit_pct, profit_usdt, targets_hit, time.time(), run_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error completing eternal run: {e}")
            return False
    
    def get_eternal_runs(self, bot_id: str, limit: int = 20) -> List[Dict]:
        """Obtém histórico de ciclos do eternal mode"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM eternal_runs 
                WHERE bot_id = ?
                ORDER BY run_number DESC
                LIMIT ?
            ''', (bot_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting eternal runs: {e}")
            return []
    
    def get_eternal_runs_summary(self, bot_id: str) -> Dict:
        """Obtém resumo dos ciclos do eternal mode"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_runs,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_runs,
                    SUM(CASE WHEN profit_pct > 0 THEN 1 ELSE 0 END) as profitable_runs,
                    SUM(COALESCE(profit_usdt, 0)) as total_profit_usdt,
                    AVG(CASE WHEN status = 'completed' THEN profit_pct ELSE NULL END) as avg_profit_pct,
                    MAX(profit_pct) as best_run_pct,
                    MIN(CASE WHEN profit_pct < 0 THEN profit_pct ELSE NULL END) as worst_run_pct
                FROM eternal_runs 
                WHERE bot_id = ?
            ''', (bot_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return {}
        except Exception as e:
            logger.error(f"Error getting eternal runs summary: {e}")
            return {}
    
    # --- RISK METRICS ---
    
    def add_risk_metric(self, metric_name: str, metric_value: float,
                       symbol: str = None) -> bool:
        """Adiciona uma métrica de risco"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO risk_metrics (timestamp, metric_name, metric_value, symbol)
                VALUES (?, ?, ?, ?)
            ''', (time.time(), metric_name, metric_value, symbol))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding risk metric: {e}")
            return False
    
    # --- ANALYTICS ---
    
    def get_trade_statistics(self, symbol: str = None, days: int = 30) -> Dict:
        """Calcula estatísticas de trade"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            start_ts = time.time() - (days * 86400)
            query = "SELECT * FROM trades WHERE timestamp >= ?"
            params = [start_ts]
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            cursor.execute(query, params)
            trades = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            if not trades:
                return {}
            
            total_trades = len(trades)
            profitable = [t for t in trades if t.get('profit', 0) > 0]
            losing = [t for t in trades if t.get('profit', 0) < 0]
            
            total_profit = sum(t.get('profit', 0) for t in trades)
            total_commission = sum(t.get('commission', 0) for t in trades)
            
            win_rate = len(profitable) / total_trades if total_trades > 0 else 0
            
            avg_win = (sum(t['profit'] for t in profitable) / len(profitable) 
                      if profitable else 0)
            avg_loss = (sum(t['profit'] for t in losing) / len(losing) 
                       if losing else 0)
            
            profit_factor = (sum(t['profit'] for t in profitable) / 
                           abs(sum(t['profit'] for t in losing)) 
                           if losing and sum(t['profit'] for t in losing) != 0 
                           else 0)
            
            return {
                'total_trades': total_trades,
                'winning_trades': len(profitable),
                'losing_trades': len(losing),
                'win_rate': win_rate,
                'total_profit': total_profit,
                'total_commission': total_commission,
                'net_profit': total_profit - total_commission,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor
            }
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}

# Instância Global
db = DatabaseManager()
def _drop_and_create_tables():
    """
    ATENÇÃO:
    Este método APAGA TODOS OS DADOS do banco.
    Use apenas para reset completo de schema.
    """

    conn = db.get_connection()
    cur = conn.cursor()

    # ==========================
    # DROP TABLES (ordem segura)
    # ==========================
    cur.execute("DROP TABLE IF EXISTS trades")
    cur.execute("DROP TABLE IF EXISTS equity_snapshots")
    cur.execute("DROP TABLE IF EXISTS bot_sessions")
    cur.execute("DROP TABLE IF EXISTS bot_logs")

    # ==========================
    # CREATE TABLES
    # ==========================

    # --- Sessões de Bot ---
    cur.execute("""
        CREATE TABLE bot_sessions (
            id TEXT PRIMARY KEY,
            symbol TEXT,
            mode TEXT,
            entry_price REAL,
            targets TEXT,
            size REAL,
            funds REAL,
            start_ts INTEGER,
            end_ts INTEGER,
            status TEXT,
            total_profit REAL,
            dry_run INTEGER
        )
    """)

    # --- Trades ---
    cur.execute("""
        CREATE TABLE trades (
            id TEXT PRIMARY KEY,
            timestamp INTEGER,
            symbol TEXT,
            side TEXT,
            price REAL,
            size REAL,
            funds REAL,
            profit REAL,
            bot_id TEXT,
            strategy TEXT,
            dry_run INTEGER,
            metadata TEXT
        )
    """)

    # --- Equity Snapshots (BASE DOS GRÁFICOS) ---
    cur.execute("""
        CREATE TABLE equity_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            balance_usdt REAL NOT NULL,
            btc_price REAL,
            average_cost REAL,
            num_positions INTEGER,
            bot_id TEXT
        )
    """)

    # --- Logs do Bot ---
    cur.execute("""
        CREATE TABLE bot_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER,
            level TEXT,
            message TEXT,
            bot_id TEXT
        )
    """)

    # --- Learning Stats ---
    cur.execute("""
        CREATE TABLE learning_stats (
            symbol TEXT NOT NULL,
            param_name TEXT NOT NULL,
            param_value REAL NOT NULL,
            mean_reward REAL NOT NULL,
            n INTEGER NOT NULL,
            PRIMARY KEY (symbol, param_name, param_value)
        )
    """)

    # --- Learning History ---
    cur.execute("""
        CREATE TABLE learning_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            param_name TEXT NOT NULL,
            param_value REAL NOT NULL,
            reward REAL NOT NULL,
            timestamp REAL NOT NULL
        )
    """)

    # ==========================
    # INDEXES (performance)
    # ==========================
    cur.execute("CREATE INDEX idx_equity_ts ON equity_snapshots(timestamp)")
    cur.execute("CREATE INDEX idx_equity_bot ON equity_snapshots(bot_id)")
    cur.execute("CREATE INDEX idx_trades_bot ON trades(bot_id)")
    cur.execute("CREATE INDEX idx_logs_bot ON bot_logs(bot_id)")
    cur.execute("CREATE INDEX idx_learning_history_symbol_param ON learning_history(symbol, param_name)")
    cur.execute("CREATE INDEX idx_learning_history_timestamp ON learning_history(timestamp)")
    cur.execute("CREATE INDEX idx_learning_stats_symbol_param ON learning_stats(symbol, param_name)")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    print("⚠️  RESET COMPLETO DO DATABASE ⚠️")
    confirm = input("Digite 'RESET' para confirmar: ").strip()

    if confirm == "RESET":
        _drop_and_create_tables()
        print("✅ Database resetado com sucesso.")
    else:
        print("❌ Operação cancelada.")


# Standalone functions for compatibility
def get_logs(limit=1000):
    """Get recent logs from all bots"""
    try:
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM bot_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return []

def get_trades(bot_id=None):
    """Get trades, optionally filtered by bot_id"""
    return db.get_trades(bot_id)

def get_bot_sessions():
    """Get active bot sessions"""
    return db.get_active_bots()

