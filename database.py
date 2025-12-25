# kucoin_app/database.py
# SQLite database manager for trades, logs, and equity tracking

import sqlite3
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "trades.db"

class DatabaseManager:
    """Gerencia todas as operações do banco de dados"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Obtém a conexão com o banco de dados com row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Inicializa o esquema do banco de dados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela Trades
        cursor.execute('''
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
        cursor.execute('''
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
        cursor.execute('''
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
        cursor.execute('''
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
        cursor.execute('''
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                symbol TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Cria índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_sessions_status ON bot_sessions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_logs_bot_id ON bot_logs(bot_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_equity_timestamp ON equity_snapshots(timestamp)')
        
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
            query += " GROUP BY order_id"
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        
        # Converte para lista de dicts
        return [
            {
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

    # ==========================
    # INDEXES (performance)
    # ==========================
    cur.execute("CREATE INDEX idx_equity_ts ON equity_snapshots(timestamp)")
    cur.execute("CREATE INDEX idx_equity_bot ON equity_snapshots(bot_id)")
    cur.execute("CREATE INDEX idx_trades_bot ON trades(bot_id)")
    cur.execute("CREATE INDEX idx_logs_bot ON bot_logs(bot_id)")

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

