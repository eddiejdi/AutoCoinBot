# kucoin_app/database.py
# SQLite database manager for trades, logs, and equity tracking

import os
from pathlib import Path as _Path
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent

# Load .env if available to allow configuring DB path via TRADES_DB
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

if load_dotenv:
    # Try to load from project root (parent of autocoinbot/)
    try:
        project_root = _Path(__file__).resolve().parent.parent
        load_dotenv(dotenv_path=project_root / '.env')
    except Exception:
        pass
    # Fallback to current working directory
    try:
        load_dotenv(dotenv_path=_Path.cwd() / '.env')
    except Exception:
        pass
    # Fallback to default load_dotenv() behavior
    try:
        load_dotenv()
    except Exception:
        pass

DB_DSN = os.environ.get("DATABASE_URL") or os.environ.get("TRADES_DB")

class DatabaseManager:
    # --- LEARNING (APRENDIZADO) ---
    def get_learning_symbols(self) -> list:
        """Retorna todos os símbolos presentes em learning_stats."""
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT DISTINCT symbol FROM learning_stats ORDER BY symbol")
            rows = cur.fetchall()
            return [r.get('symbol') for r in rows if r.get('symbol')]
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
                WHERE symbol = %s AND param_name = %s
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
                WHERE symbol = %s AND param_name = %s
                ORDER BY timestamp DESC
                LIMIT %s
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

    def get_best_learned_param(self, symbol: str, param_name: str) -> dict | None:
        """Retorna o melhor parâmetro aprendido (maior mean_reward com n >= 3).
        
        Returns:
            Dict com param_value, mean_reward, n ou None se não houver dados suficientes.
        """
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT param_value, mean_reward, n
                FROM learning_stats
                WHERE symbol = %s AND param_name = %s AND n >= 3
                ORDER BY mean_reward DESC
                LIMIT 1
                """,
                (symbol, param_name)
            )
            row = cur.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Erro ao buscar best_learned_param: {e}")
            return None
        finally:
            conn.close()

    def get_learning_summary(self, symbol: str) -> dict:
        """Retorna resumo de aprendizado para um símbolo.
        
        Returns:
            Dict com total_rewards, positive_rewards, negative_rewards,
            avg_reward, best_params por param_name.
        """
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            # Estatísticas gerais do histórico
            cur.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN reward > 0 THEN 1 ELSE 0 END) as positive,
                    SUM(CASE WHEN reward < 0 THEN 1 ELSE 0 END) as negative,
                    AVG(reward) as avg_reward,
                    SUM(reward) as total_reward
                FROM learning_history
                WHERE symbol = %s
                """,
                (symbol,)
            )
            row = cur.fetchone()
            summary = dict(row) if row else {}
            
            # Melhores parâmetros por tipo
            cur.execute(
                """
                SELECT param_name, param_value, mean_reward, n
                FROM learning_stats
                WHERE symbol = %s AND n >= 3
                ORDER BY param_name, mean_reward DESC
                """,
                (symbol,)
            )
            rows = cur.fetchall()
            
            best_params = {}
            for r in rows:
                pname = r['param_name']
                if pname not in best_params:
                    best_params[pname] = {
                        'value': r['param_value'],
                        'mean_reward': r['mean_reward'],
                        'n': r['n']
                    }
            
            summary['best_params'] = best_params
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao buscar learning_summary: {e}")
            return {}
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
            placeholders = ','.join(['%s'] * len(candidates))
            cur.execute(f"""
                SELECT param_value, mean_reward, n
                FROM learning_stats
                WHERE symbol = %s AND param_name = %s AND param_value IN ({placeholders})
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
                VALUES (%s, %s, %s, %s, %s)
            """, (symbol, param_name, param_value, reward, time.time()))
            
            # Atualiza ou insere estatísticas
            cur.execute("""
                SELECT mean_reward, n FROM learning_stats
                WHERE symbol = %s AND param_name = %s AND param_value = %s
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
                    SET mean_reward = %s, n = %s
                    WHERE symbol = %s AND param_name = %s AND param_value = %s
                """, (new_mean, new_n, symbol, param_name, param_value))
            else:
                # Insere novo registro
                cur.execute("""
                    INSERT INTO learning_stats (symbol, param_name, param_value, mean_reward, n)
                    VALUES (%s, %s, %s, %s, %s)
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

    def __init__(self, db_dsn: str | None = DB_DSN, auto_init: bool = True):
        self.db_dsn = db_dsn
        if not self.db_dsn:
            raise RuntimeError("DATABASE_URL/TRADES_DB nÇœo configurado para PostgreSQL")
        if auto_init:
            self.init_database()
    
    def get_connection(self):
        """Obtém a conexão com o banco de dados com row factory"""
        return psycopg.connect(self.db_dsn, row_factory=dict_row)
    
    def init_database(self):
        """Inicializa o esquema do banco de dados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela Trades
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                timestamp DOUBLE PRECISION NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                price DOUBLE PRECISION NOT NULL,
                size DOUBLE PRECISION,
                funds DOUBLE PRECISION,
                profit DOUBLE PRECISION,
                commission DOUBLE PRECISION,
                order_id TEXT,
                bot_id TEXT,
                strategy TEXT,
                dry_run BOOLEAN DEFAULT TRUE,
                metadata JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        
        # Tabela Bot sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_sessions (
                id TEXT PRIMARY KEY,
                pid INTEGER,
                symbol TEXT NOT NULL,
                mode TEXT NOT NULL,
                entry_price DOUBLE PRECISION NOT NULL,
                targets TEXT,
                trailing_stop_pct DOUBLE PRECISION,
                stop_loss_pct DOUBLE PRECISION,
                size DOUBLE PRECISION,
                funds DOUBLE PRECISION,
                start_ts DOUBLE PRECISION NOT NULL,
                end_ts DOUBLE PRECISION,
                status TEXT DEFAULT 'running',
                executed_parts TEXT,
                remaining_fraction DOUBLE PRECISION,
                total_profit DOUBLE PRECISION,
                dry_run BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        
        # Tabela Equity snapshots (AGORA COM average_cost)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equity_snapshots (
                id SERIAL PRIMARY KEY,
                timestamp DOUBLE PRECISION NOT NULL,
                balance_usdt DOUBLE PRECISION NOT NULL,
                bot_id TEXT,
                btc_price DOUBLE PRECISION,
                average_cost DOUBLE PRECISION,  -- NOVO: Custo Médio Ponderado da Posição
                num_positions INTEGER,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        
        # Tabela Eternal Runs - histórico de ciclos do eternal mode
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS eternal_runs (
                id SERIAL PRIMARY KEY,
                bot_id TEXT NOT NULL,
                run_number INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                entry_price DOUBLE PRECISION NOT NULL,
                exit_price DOUBLE PRECISION,
                profit_pct DOUBLE PRECISION,
                profit_usdt DOUBLE PRECISION,
                targets_hit INTEGER DEFAULT 0,
                total_targets INTEGER DEFAULT 0,
                start_ts DOUBLE PRECISION NOT NULL,
                end_ts DOUBLE PRECISION,
                status TEXT DEFAULT 'running',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        
        # Tabela Bot logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_logs (
                id SERIAL PRIMARY KEY,
                bot_id TEXT NOT NULL,
                timestamp DOUBLE PRECISION NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                data TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        
        # Tabela Risk metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_metrics (
                id SERIAL PRIMARY KEY,
                timestamp DOUBLE PRECISION NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value DOUBLE PRECISION NOT NULL,
                symbol TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        
        # Tabela Learning stats (estatísticas de aprendizado por parâmetro)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_stats (
                symbol TEXT NOT NULL,
                param_name TEXT NOT NULL,
                param_value DOUBLE PRECISION NOT NULL,
                mean_reward DOUBLE PRECISION NOT NULL,
                n INTEGER NOT NULL,
                PRIMARY KEY (symbol, param_name, param_value)
            )
        ''')
        
        # Tabela Learning history (histórico de recompensas)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_history (
                id SERIAL PRIMARY KEY,
                symbol TEXT NOT NULL,
                param_name TEXT NOT NULL,
                param_value DOUBLE PRECISION NOT NULL,
                reward DOUBLE PRECISION NOT NULL,
                timestamp DOUBLE PRECISION NOT NULL
            )
        ''')
        
        # Cria índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_sessions_status ON bot_sessions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_logs_bot_id ON bot_logs(bot_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_equity_timestamp ON equity_snapshots(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_history_symbol_param ON learning_history(symbol, param_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_history_timestamp ON learning_history(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_stats_symbol_param ON learning_stats(symbol, param_name)')       
        
        conn.commit()
        conn.close()
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

        return [r.get('bot_id') for r in rows if r.get('bot_id')]


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
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                bool(trade_data.get('dry_run', True)),
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
                WHERE bot_id = %s
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

        return [dict(r) for r in rows]

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
            query += " AND bot_id = %s"
            params.append(bot_id)
            
        if only_real:
            query += " AND dry_run = false"
        
        order_clause = "ORDER BY timestamp DESC"
        if group_by_order_id:
            query = query.replace(
                "SELECT id, timestamp, symbol, side, price, size, funds, profit, \n                   commission, order_id, bot_id, strategy, dry_run, metadata",
                "SELECT DISTINCT ON (order_id) id, timestamp, symbol, side, price, size, funds, profit, \n                   commission, order_id, bot_id, strategy, dry_run, metadata"
            )
            order_clause = "ORDER BY order_id, timestamp DESC"
        
        query += f" {order_clause} LIMIT %s"
        params.append(limit)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        
        return [dict(r) for r in rows]

    
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
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                bool(session_data.get('dry_run', True))
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
            
            set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
            values = list(updates.values()) + [bot_id]
            
            cursor.execute(f"UPDATE bot_sessions SET {set_clause} WHERE id = %s", values)
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
                VALUES (%s, %s, %s, %s, %s)
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
                WHERE timestamp >= %s 
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
                VALUES (%s, %s, %s, %s, %s)
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
                WHERE bot_id = %s 
                ORDER BY timestamp DESC
                LIMIT %s
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
                VALUES (%s, %s, %s, %s, %s, %s, 'running')
                RETURNING id
            ''', (bot_id, run_number, symbol, entry_price, total_targets, time.time()))
            
            row = cursor.fetchone()
            run_id = row["id"] if row else None
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
                SET exit_price = %s, profit_pct = %s, profit_usdt = %s,
                    targets_hit = %s, end_ts = %s, status = 'completed'
                WHERE id = %s
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
                WHERE bot_id = %s
                ORDER BY run_number DESC
                LIMIT %s
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
                WHERE bot_id = %s
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
                VALUES (%s, %s, %s, %s)
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
            query = "SELECT * FROM trades WHERE timestamp >= %s"
            params = [start_ts]
            
            if symbol:
                query += " AND symbol = %s"
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

# Instância Global - criada sob demanda para evitar erros em imports
db = None

def get_db():
    """Retorna a instância global do DatabaseManager (lazy initialization)."""
    global db
    if db is None:
        db = DatabaseManager()
    return db

def _drop_and_create_tables():
    """
    ATENÇÃO:
    Este método APAGA TODOS OS DADOS do banco.
    Use apenas para reset completo de schema.
    """

    conn = get_db().get_connection()
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
