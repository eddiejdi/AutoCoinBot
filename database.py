# kucoin_app/database.py
# SQLite database manager for trades, logs, and equity tracking

import sqlite3
import json
import time
import logging
import threading
import queue as _queue
import atexit
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "trades.db"

class DatabaseManager:
    """Gerencia todas as operações do banco de dados"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        # Write queue for serialized DB write operations
        self._write_queue: _queue.Queue = _queue.Queue()
        self._worker_running = True
        self._worker_thread = threading.Thread(target=self._queue_worker, name="DBWriteWorker", daemon=True)
        self._worker_thread.start()

        # Ensure graceful stop on process exit
        atexit.register(self._stop_queue_worker)

        # History batcher config
        self._history_batch: list[tuple] = []
        self._history_lock = threading.Lock()
        self._history_batch_size = 100
        self._history_flush_interval = 2.0
        self._history_flusher_running = True
        self._history_flusher_thread = threading.Thread(target=self._history_flusher, name="HistoryFlusher", daemon=True)
        self._history_flusher_thread.start()

        self.init_database()
    
    def get_connection(self):
        """Obtém a conexão com o banco de dados com row factory"""
        # Configure connection with pragmatic defaults for better concurrency
        # and WAL behaviour. `check_same_thread=False` allows using the
        # connection from different threads if necessary (use with care).
        conn = sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            # Enable WAL for better read/write concurrency
            cur.execute("PRAGMA journal_mode=WAL;")
            # Faster but slightly less durable sync; acceptable for many apps
            cur.execute("PRAGMA synchronous=NORMAL;")
            # Automatic checkpoint threshold (pages) - tune as needed
            cur.execute("PRAGMA wal_autocheckpoint=1000;")
            # Avoid immediate busy errors on contention
            cur.execute("PRAGMA busy_timeout=5000;")
            cur.close()
        except Exception:
            # If any PRAGMA fails, still return the connection
            pass
        return conn

    # ----------------
    # Queue system
    # ----------------

    class _TaskResult:
        def __init__(self):
            self._event = threading.Event()
            self.result: Any = None
            self.exception: Optional[BaseException] = None

        def set_result(self, value: Any):
            self.result = value
            self._event.set()

        def set_exception(self, exc: BaseException):
            self.exception = exc
            self._event.set()

        def wait(self, timeout: Optional[float] = None):
            self._event.wait(timeout)
            if self.exception:
                raise self.exception
            return self.result

    def _queue_worker(self):
        """Worker que processa callables serialmente.

        Cada callable deve aceitar uma conexão SQLite como primeiro argumento:
            def my_task(conn, ...):
                cur = conn.cursor(); cur.execute(...)

        O worker abre uma nova conexão para cada tarefa, executa a função,
        commita e fecha a conexão.
        """
        while self._worker_running:
            try:
                item = self._write_queue.get()
            except Exception:
                continue
            if item is None:
                break
            func, args, kwargs, task_res = item
            try:
                conn = self.get_connection()
                try:
                    # Call the function passing the connection first
                    res = func(conn, *args, **kwargs)
                    conn.commit()
                    task_res.set_result(res)
                except Exception as e:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    task_res.set_exception(e)
                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass
            finally:
                try:
                    self._write_queue.task_done()
                except Exception:
                    pass

    def _stop_queue_worker(self, timeout: float = 5.0):
        """Para o worker de forma ordenada."""
        if not self._worker_running:
            return
        self._worker_running = False
        # Enfileira sentinel para acordar o worker
        try:
            self._write_queue.put_nowait(None)
        except Exception:
            pass
        # Aguarda join
        try:
            self._worker_thread.join(timeout)
        except Exception:
            pass
        # Stop history flusher and flush remaining
        try:
            self._history_flusher_running = False
            # Trigger flush
            self._flush_history_batch()
            self._history_flusher_thread.join(1.0)
        except Exception:
            pass

    def enqueue_write(self, func, *args, **kwargs):
        """Enfileira uma callable que receberá uma conexão SQLite como primeiro arg.

        Retorna um objeto `TaskResult` com método `wait()` para obter o resultado
        (ou lançar a exceção ocorrida).
        """
        task = DatabaseManager._TaskResult()
        self._write_queue.put((func, args, kwargs, task))
        return task

    def enqueue_sql(self, sql: str, params: tuple = ()): 
        """Convenience: enfileira execução SQL simples (INSERT/UPDATE/DELETE).

        Retorna `TaskResult`.
        """
        def _exec(conn, s, p):
            cur = conn.cursor()
            cur.execute(s, p)
            return cur.rowcount

        return self.enqueue_write(_exec, sql, params)

    # ----------------
    # Bot learning history batcher
    # ----------------

    def add_learning_history_entry(self, timestamp: float, symbol: str, param_name: str, param_value: float, reward: float):
        """Adiciona uma entrada ao batch de `bot_learning_history`.

        Será flushado quando o batch atingir `_history_batch_size` ou
        no intervalo `_history_flush_interval`.
        """
        entry = (float(timestamp), str(symbol), str(param_name), float(param_value), float(reward))
        with self._history_lock:
            self._history_batch.append(entry)
            if len(self._history_batch) >= self._history_batch_size:
                # flush de forma assíncrona via fila
                batch = list(self._history_batch)
                self._history_batch.clear()
                return self.enqueue_write(self._write_history_batch, batch)
        return None

    def _history_flusher(self):
        while self._history_flusher_running:
            time.sleep(self._history_flush_interval)
            try:
                self._flush_history_batch()
            except Exception:
                pass

    def _flush_history_batch(self):
        with self._history_lock:
            if not self._history_batch:
                return
            batch = list(self._history_batch)
            self._history_batch.clear()
        # Enfileira para escrita em lote
        return self.enqueue_write(self._write_history_batch, batch)

    @staticmethod
    def _write_history_batch(conn, batch: list[tuple]):
        cur = conn.cursor()
        cur.executemany(
            """
            INSERT INTO bot_learning_history(timestamp, symbol, param_name, param_value, reward)
            VALUES (?, ?, ?, ?, ?)
            """,
            batch,
        )
        return cur.rowcount
    
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

        # Tabela de cotas/alocações por bot (evita dois bots usarem o mesmo saldo/posição)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_quotas (
                bot_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                asset TEXT NOT NULL,
                qty REAL NOT NULL,
                entry_price REAL,
                status TEXT DEFAULT 'allocated',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                released_ts REAL
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

        # Tabela de auto-aprendizado (parâmetros adaptativos por símbolo)
        # Um registro por (symbol, param_name, param_value) para suportar bandit (A/B) simples.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_learning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                param_name TEXT NOT NULL,
                param_value REAL NOT NULL,
                n INTEGER DEFAULT 0,
                mean_reward REAL DEFAULT 0,
                last_reward REAL,
                last_ts REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, param_name, param_value)
            )
        ''')

        # Histórico de recompensas (para gráficos de evolução)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_learning_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                symbol TEXT NOT NULL,
                param_name TEXT NOT NULL,
                param_value REAL NOT NULL,
                reward REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Cria índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_order_id ON trades(order_id)')

        # Evita duplicar o mesmo evento de trade para a mesma order_id/strategy/bot/side.
        # (Permite coexistir kucoin_fill + target_* pois strategy difere.)
        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uniq_trades_order_strategy_bot_side
            ON trades(order_id, strategy, bot_id, side)
            WHERE order_id IS NOT NULL AND order_id != ''
            """
        )
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_quotas_asset_status ON bot_quotas(asset, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_sessions_status ON bot_sessions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_logs_bot_id ON bot_logs(bot_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_equity_timestamp ON equity_snapshots(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_learning_symbol_param ON bot_learning(symbol, param_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_learning_hist_symbol_param_ts ON bot_learning_history(symbol, param_name, timestamp)')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

        # Migration: add balances and bot_id columns to equity_snapshots if not exists
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(equity_snapshots)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'balances' not in columns:
                cursor.execute("ALTER TABLE equity_snapshots ADD COLUMN balances TEXT")
                conn.commit()
                logger.info("Added balances column to equity_snapshots")
            if 'bot_id' not in columns:
                cursor.execute("ALTER TABLE equity_snapshots ADD COLUMN bot_id TEXT")
                conn.commit()
                logger.info("Added bot_id column to equity_snapshots")
            conn.close()
        except Exception as e:
            logger.warning(f"Could not add columns to equity_snapshots: {e}")

    def wal_checkpoint(self, mode: str = "PASSIVE") -> bool:
        """Executa um checkpoint WAL.

        mode: PASSIVE | FULL | RESTART
        Retorna True se o comando foi executado sem exceção.
        """
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(f"PRAGMA wal_checkpoint({mode})")
            # PRAGMA wal_checkpoint may return a result; commit to be safe
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.warning(f"wal_checkpoint failed: {e}")
            return False

    # --- AUTO-LEARNING (bandit) ---

    def choose_bandit_param(
        self,
        symbol: str,
        param_name: str,
        candidates: list[float],
        epsilon: float = 0.2,
    ) -> float:
        """Escolhe um valor de parâmetro via epsilon-greedy.

        Persistência em `bot_learning`:
        - reward = métrica escalar (ex.: profit_pct no SELL)
        - mean_reward = média incremental
        """
        sym = str(symbol or "").upper().strip()
        pname = str(param_name or "").strip()
        if not sym or not pname:
            return float(candidates[0])

        try:
            eps = float(epsilon)
        except Exception:
            eps = 0.2
        eps = max(0.0, min(eps, 1.0))

        # Ensure candidates are valid floats
        vals: list[float] = []
        for c in candidates or []:
            try:
                vals.append(float(c))
            except Exception:
                continue
        if not vals:
            return 0.5

        # Ensure rows exist via write-queue to avoid concurrent write locks
        def _ensure_rows(conn, sym_v, pname_v, vals_v):
            cur = conn.cursor()
            for v in vals_v:
                cur.execute(
                    """
                    INSERT OR IGNORE INTO bot_learning(symbol, param_name, param_value, n, mean_reward, last_ts)
                    VALUES (?, ?, ?, 0, 0, ?)
                    """,
                    (sym_v, pname_v, float(v), time.time()),
                )
            return True

        try:
            # enqueue and wait to ensure rows are present
            task = self.enqueue_write(_ensure_rows, sym, pname, vals)
            task.wait()
        except Exception:
            # If enqueue fails, fall back to direct writes (best-effort)
            try:
                conn = self.get_connection()
                cur = conn.cursor()
                for v in vals:
                    cur.execute(
                        """
                        INSERT OR IGNORE INTO bot_learning(symbol, param_name, param_value, n, mean_reward, last_ts)
                        VALUES (?, ?, ?, 0, 0, ?)
                        """,
                        (sym, pname, float(v), time.time()),
                    )
                conn.commit()
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

        # Load stats (reads can use their own connection)
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT param_value, n, mean_reward
                FROM bot_learning
                WHERE symbol = ? AND param_name = ?
                """,
                (sym, pname),
            )
            rows = cur.fetchall() or []
        finally:
            conn.close()

        stats: dict[float, tuple[int, float]] = {}
        for r in rows:
            try:
                v = float(r[0])
                n = int(r[1] or 0)
                m = float(r[2] or 0.0)
                stats[v] = (n, m)
            except Exception:
                continue

        import random as _rnd
        if _rnd.random() < eps:
            return float(_rnd.choice(vals))

        # Pick best mean_reward; break ties by lower n (encourage exploration early)
        best_v = float(vals[0])
        best_m = None
        best_n = None
        for v in vals:
            n, m = stats.get(v, (0, 0.0))
            if best_m is None or m > best_m or (m == best_m and n < (best_n or 0)):
                best_v, best_m, best_n = float(v), float(m), int(n)
        return float(best_v)

    def update_bandit_reward(
        self,
        symbol: str,
        param_name: str,
        param_value: float,
        reward: float,
    ) -> bool:
        """Atualiza média incremental do reward para um candidato."""
        sym = str(symbol or "").upper().strip()
        pname = str(param_name or "").strip()
        if not sym or not pname:
            return False
        try:
            pv = float(param_value)
            rw = float(reward)
        except Exception:
            return False

        def _do_update(conn, sym, pname, pv, rw, now):
            cur = conn.cursor()

            cur.execute(
                """
                INSERT OR IGNORE INTO bot_learning(symbol, param_name, param_value, n, mean_reward, last_reward, last_ts)
                VALUES (?, ?, ?, 0, 0, NULL, NULL)
                """,
                (sym, pname, pv),
            )

            cur.execute(
                """
                SELECT n, mean_reward
                FROM bot_learning
                WHERE symbol = ? AND param_name = ? AND param_value = ?
                """,
                (sym, pname, pv),
            )
            row = cur.fetchone()
            n = int(row[0] or 0) if row else 0
            mean = float(row[1] or 0.0) if row else 0.0

            n2 = n + 1
            mean2 = mean + (rw - mean) / float(n2)

            cur.execute(
                """
                UPDATE bot_learning
                SET n = ?, mean_reward = ?, last_reward = ?, last_ts = ?
                WHERE symbol = ? AND param_name = ? AND param_value = ?
                """,
                (n2, mean2, rw, now, sym, pname, pv),
            )
            return True

        try:
            now = time.time()
            # Run update in queue but wait for completion to keep API synchronous
            task = self.enqueue_write(_do_update, sym, pname, pv, rw, now)
            task.wait()
            # Append history via batcher (async)
            try:
                self.add_learning_history_entry(now, sym, pname, pv, rw)
            except Exception:
                pass
            return True
        except Exception as e:
            logger.error(f"Error updating bandit reward: {e}")
            return False

    def get_learning_symbols(self) -> list[str]:
        """Lista símbolos com aprendizado registrado."""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT symbol FROM bot_learning ORDER BY symbol")
            rows = cur.fetchall() or []
            conn.close()
            return [str(r[0]) for r in rows if r and r[0]]
        except Exception:
            return []

    def get_learning_stats(self, symbol: str, param_name: str) -> list[dict]:
        """Retorna stats (n/mean_reward/last_reward/last_ts) por param_value."""
        sym = str(symbol or "").upper().strip()
        pname = str(param_name or "").strip()
        if not sym or not pname:
            return []
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT param_value, n, mean_reward, last_reward, last_ts
                FROM bot_learning
                WHERE symbol = ? AND param_name = ?
                ORDER BY mean_reward DESC, n DESC
                """,
                (sym, pname),
            )
            rows = cur.fetchall() or []
            conn.close()
            out: list[dict] = []
            for r in rows:
                out.append({
                    "param_value": r[0],
                    "n": r[1],
                    "mean_reward": r[2],
                    "last_reward": r[3],
                    "last_ts": r[4],
                })
            return out
        except Exception:
            return []

    def get_learning_history(self, symbol: str, param_name: str, limit: int = 1000) -> list[dict]:
        """Retorna histórico de recompensas para gráficos."""
        sym = str(symbol or "").upper().strip()
        pname = str(param_name or "").strip()
        if not sym or not pname:
            return []
        try:
            lim = int(limit)
        except Exception:
            lim = 1000
        lim = max(1, min(lim, 5000))
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT timestamp, param_value, reward
                FROM bot_learning_history
                WHERE symbol = ? AND param_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (sym, pname, lim),
            )
            rows = cur.fetchall() or []
            conn.close()
            out: list[dict] = []
            for r in rows:
                out.append({
                    "timestamp": r[0],
                    "param_value": r[1],
                    "reward": r[2],
                })
            return out
        except Exception:
            return []
    
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
        def _do_insert(conn, data):
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO trades (
                    id, timestamp, symbol, side, price, size, funds,
                    profit, commission, order_id, bot_id, strategy,
                    dry_run, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('id'),
                data.get('timestamp', time.time()),
                data.get('symbol'),
                data.get('side'),
                data.get('price'),
                data.get('size'),
                data.get('funds'),
                data.get('profit'),
                data.get('commission'),
                data.get('order_id'),
                data.get('bot_id'),
                data.get('strategy'),
                1 if data.get('dry_run') else 0,
                json.dumps(data.get('metadata', {}))
            ))
            return cursor.rowcount

        try:
            task = self.enqueue_write(_do_insert, trade_data)
            # Wait for completion to preserve previous synchronous behaviour
            task.wait()
            logger.info(f"Trade inserted: {trade_data.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Error inserting trade: {e}")
            return False

    def insert_trade_ignore(self, trade_data: Dict[str, Any]) -> bool:
        """Insere um novo trade se ainda não existir (por id).

        Útil para sincronizações (evita spam de erro por duplicidade).
        Retorna True se inseriu, False se já existia ou falhou.
        """
        def _do_insert_ignore(conn, data):
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO trades (
                    id, timestamp, symbol, side, price, size, funds,
                    profit, commission, order_id, bot_id, strategy,
                    dry_run, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('id'),
                data.get('timestamp', time.time()),
                data.get('symbol'),
                data.get('side'),
                data.get('price'),
                data.get('size'),
                data.get('funds'),
                data.get('profit'),
                data.get('commission'),
                data.get('order_id'),
                data.get('bot_id'),
                data.get('strategy'),
                1 if data.get('dry_run') else 0,
                json.dumps(data.get('metadata', {}))
            ))
            return (cursor.rowcount or 0) > 0

        try:
            task = self.enqueue_write(_do_insert_ignore, trade_data)
            return bool(task.wait())
        except Exception as e:
            logger.error(f"Error inserting trade (ignore): {e}")
            return False

    def get_lowest_buy_fill(self, symbol: str, only_kucoin: bool = False) -> Dict[str, float]:
        """Retorna o menor preço de BUY e a quantidade total comprada nesse preço.

        Observação: isso não faz "matching" de lotes contra SELLs; é um resumo das compras.
        Retorna: {price, qty}
        """
        if not symbol:
            return {"price": 0.0, "qty": 0.0}

        conn = self.get_connection()
        cur = conn.cursor()

        if only_kucoin:
            cur.execute(
                """
                SELECT price, size
                FROM trades
                WHERE symbol = ? AND dry_run = 0
                  AND size IS NOT NULL AND size > 0
                  AND lower(side) = 'buy'
                  AND bot_id = 'KUCOIN'
                ORDER BY price ASC, timestamp ASC
                """,
                (symbol,),
            )
        else:
            cur.execute(
                """
                SELECT price, size
                FROM trades
                WHERE symbol = ? AND dry_run = 0
                  AND size IS NOT NULL AND size > 0
                  AND lower(side) = 'buy'
                ORDER BY price ASC, timestamp ASC
                """,
                (symbol,),
            )

        rows = cur.fetchall()
        conn.close()

        if not rows:
            return {"price": 0.0, "qty": 0.0}

        # min price is first due to ORDER BY
        try:
            min_price = float(rows[0][0])
        except Exception:
            min_price = 0.0

        if min_price <= 0:
            return {"price": 0.0, "qty": 0.0}

        qty = 0.0
        eps = 1e-12
        for r in rows:
            try:
                p = float(r[0])
                s = float(r[1])
            except Exception:
                continue
            if s <= 0:
                continue
            if abs(p - min_price) <= eps:
                qty += s
            elif p > min_price:
                # because sorted asc
                break

        return {"price": float(min_price), "qty": float(qty)}

    # --- POSIÇÃO / CUSTO MÉDIO (baseado em trades reais) ---

    def get_position_average_cost(self, symbol: str, only_kucoin: bool = False) -> Dict[str, float]:
        """Calcula qty e custo médio do saldo atual (estimado) para um símbolo.

        Usa trades reais (dry_run=0) e um modelo de custo médio ponderado:
        - BUY: aumenta qty e custo
        - SELL: reduz qty e custo proporcionalmente ao custo médio atual

        Retorna: {qty, avg_cost}
        """
        symbol = (symbol or "").upper().strip()
        if not symbol:
            return {"qty": 0.0, "avg_cost": 0.0}

        conn = self.get_connection()
        cur = conn.cursor()
        if only_kucoin:
            cur.execute(
                """
                SELECT side, price, size
                FROM trades
                WHERE symbol = ? AND dry_run = 0 AND size IS NOT NULL AND size > 0
                  AND bot_id = 'KUCOIN'
                ORDER BY timestamp ASC
                """,
                (symbol,),
            )
        else:
            cur.execute(
                """
                SELECT side, price, size
                FROM trades
                WHERE symbol = ? AND dry_run = 0 AND size IS NOT NULL AND size > 0
                ORDER BY timestamp ASC
                """,
                (symbol,),
            )
        rows = cur.fetchall()
        conn.close()

        qty = 0.0
        cost = 0.0

        for side, price, size in rows:
            try:
                side_s = str(side).lower().strip()
            except Exception:
                side_s = ""
            try:
                p = float(price)
                q = float(size)
            except Exception:
                continue
            if q <= 0 or p <= 0:
                continue

            if side_s == "buy":
                qty += q
                cost += p * q
            elif side_s == "sell":
                if qty <= 0:
                    continue
                avg = (cost / qty) if qty > 0 else 0.0
                sell_qty = min(q, qty)
                qty -= sell_qty
                cost -= avg * sell_qty
                if qty <= 0:
                    qty = 0.0
                    cost = 0.0

        avg_cost = (cost / qty) if qty > 0 else 0.0
        return {"qty": float(qty), "avg_cost": float(avg_cost)}

    # --- COTAS / ALOCAÇÕES ---

    def get_allocated_qty(self, asset: str, status: str = "allocated") -> float:
        asset = (asset or "").upper().strip()
        if not asset:
            return 0.0
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COALESCE(SUM(qty), 0)
            FROM bot_quotas
            WHERE asset = ? AND status = ?
            """,
            (asset, status),
        )
        row = cur.fetchone()
        conn.close()
        try:
            return float(row[0] or 0.0)
        except Exception:
            return 0.0

    def upsert_bot_quota(self, bot_id: str, symbol: str, asset: str, qty: float, entry_price: float | None = None) -> bool:
        """Cria/atualiza uma cota alocada para um bot."""
        bot_id = str(bot_id)
        symbol = (symbol or "").upper().strip()
        asset = (asset or "").upper().strip()
        try:
            qty_f = float(qty)
        except Exception:
            return False
        if qty_f <= 0 or not bot_id or not symbol or not asset:
            return False

        def _do_upsert(conn, bot_id, symbol, asset, qty_f, entry_price):
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO bot_quotas (bot_id, symbol, asset, qty, entry_price, status, released_ts)
                VALUES (?, ?, ?, ?, ?, 'allocated', NULL)
                ON CONFLICT(bot_id) DO UPDATE SET
                    symbol = excluded.symbol,
                    asset = excluded.asset,
                    qty = excluded.qty,
                    entry_price = excluded.entry_price,
                    status = 'allocated',
                    released_ts = NULL
                """,
                (bot_id, symbol, asset, qty_f, float(entry_price) if entry_price is not None else None),
            )
            return True

        try:
            task = self.enqueue_write(_do_upsert, bot_id, symbol, asset, qty_f, entry_price)
            return bool(task.wait())
        except Exception as e:
            logger.error(f"Error upserting bot quota: {e}")
            return False

    def release_bot_quota(self, bot_id: str) -> bool:
        bot_id = str(bot_id)
        if not bot_id:
            return False
        def _do_release(conn, bot_id):
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE bot_quotas
                SET status = 'released', released_ts = ?
                WHERE bot_id = ?
                """,
                (time.time(), bot_id),
            )
            return True

        try:
            task = self.enqueue_write(_do_release, bot_id)
            return bool(task.wait())
        except Exception as e:
            logger.error(f"Error releasing bot quota: {e}")
            return False
    
    def get_trades(
        self,
        bot_id: str | None = None,
        start_ts: float | None = None,
        limit: int | None = None,
        realized_only: bool = True,
    ):
        """Retorna trades simplificados (timestamp/profit/bot_id).

        Por padrão retorna apenas PnL realizado (SELL) para evitar que BUYs sejam
        contabilizados como prejuízo (entrada/custo).
        """
        conn = self.get_connection()
        cur = conn.cursor()

        where: list[str] = []
        params: list[Any] = []
        if bot_id:
            where.append("bot_id = ?")
            params.append(bot_id)
        if start_ts is not None:
            where.append("timestamp >= ?")
            params.append(float(start_ts))
        if realized_only:
            where.append("side = 'sell'")
            where.append("profit IS NOT NULL")

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        try:
            limit_i = int(limit) if limit is not None else 0
        except Exception:
            limit_i = 0
        limit_sql = f"LIMIT {limit_i}" if limit_i and limit_i > 0 else ""

        cur.execute(
            f"""
            SELECT timestamp, profit, bot_id
            FROM trades
            {where_sql}
            ORDER BY timestamp
            {limit_sql}
            """,
            tuple(params),
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

    def get_trade_history(
        self,
        limit: int = 2000,
        bot_id: str | None = None,
        only_real: bool = False,
        start_ts: float | None = None,
        end_ts: float | None = None,
        symbol: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Retorna o histórico completo de trades (mais recente primeiro).

        Mantém um limite por padrão para evitar travar a UI.
        """
        try:
            limit_i = int(limit) if limit is not None else 2000
        except Exception:
            limit_i = 2000
        if limit_i <= 0:
            limit_i = 2000

        conn = self.get_connection()
        cur = conn.cursor()

        where_clauses: List[str] = []
        params: List[Any] = []

        if bot_id:
            where_clauses.append("bot_id = ?")
            params.append(bot_id)
        if only_real:
            where_clauses.append("dry_run = 0")
        if start_ts is not None:
            where_clauses.append("timestamp >= ?")
            params.append(float(start_ts))
        if end_ts is not None:
            where_clauses.append("timestamp <= ?")
            params.append(float(end_ts))
        if symbol:
            where_clauses.append("symbol = ?")
            params.append(symbol)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        sql = f"""
            SELECT
                id, timestamp, symbol, side, price, size, funds,
                profit, commission, order_id, bot_id, strategy, dry_run, metadata
            FROM trades
            {where_sql}
            ORDER BY timestamp DESC
            LIMIT ?
        """
        params.append(limit_i)
        cur.execute(sql, tuple(params))

        rows = cur.fetchall()
        conn.close()

        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append({
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
            })
        return out

    def get_trade_history_grouped(
        self,
        limit: int = 2000,
        bot_id: str | None = None,
        only_real: bool = False,
        start_ts: float | None = None,
        end_ts: float | None = None,
        symbol: str | None = None,
        group_by_order_id: bool = True,
    ) -> List[Dict[str, Any]]:
        """Histórico de trades com dedupe por order_id.

        Une eventos como `kucoin_fill` + `target_*` na mesma linha quando compartilham
        o mesmo `order_id`.

        - Campos numéricos (size/funds/commission/price) preferem o registro `kucoin_fill`.
        - `profit` representa apenas PnL realizado (SELL); BUY retorna None.
        - `strategy` e `bot_id` viram listas (CSV) das fontes agrupadas.
        """

        rows = self.get_trade_history(
            limit=limit,
            bot_id=bot_id,
            only_real=only_real,
            start_ts=start_ts,
            end_ts=end_ts,
            symbol=symbol,
        )
        if not group_by_order_id:
            return rows

        grouped: dict[str, Dict[str, Any]] = {}

        def _norm_order_id(v: Any) -> str | None:
            if v is None:
                return None
            s = str(v).strip()
            return s if s else None

        for r in rows:
            oid = _norm_order_id(r.get("order_id"))
            key = oid or str(r.get("id"))

            g = grouped.get(key)
            if g is None:
                g = {
                    "id": r.get("id"),
                    "timestamp": r.get("timestamp"),
                    "symbol": r.get("symbol"),
                    "side": r.get("side"),
                    "price": r.get("price"),
                    "size": r.get("size"),
                    "funds": r.get("funds"),
                    "profit": None,
                    "commission": None,
                    "order_id": oid,
                    "bot_id": r.get("bot_id"),
                    "strategy": r.get("strategy"),
                    "dry_run": r.get("dry_run"),
                    "metadata": r.get("metadata"),
                    "_bots": set(),
                    "_strategies": set(),
                    "_commission_sum": 0.0,
                    "_has_commission": False,
                }
                grouped[key] = g

            if r.get("bot_id") is not None:
                try:
                    g["_bots"].add(str(r.get("bot_id")))
                except Exception:
                    pass
            if r.get("strategy") is not None:
                try:
                    g["_strategies"].add(str(r.get("strategy")))
                except Exception:
                    pass

            # Preferir fill oficial para números.
            if str(r.get("strategy") or "").strip() == "kucoin_fill":
                if r.get("price") is not None:
                    g["price"] = r.get("price")
                if r.get("size") is not None:
                    g["size"] = r.get("size")
                if r.get("funds") is not None:
                    g["funds"] = r.get("funds")
                # Fees can be split across multiple fills for the same order_id.
                try:
                    c = r.get("commission")
                    if c is not None:
                        g["_commission_sum"] = float(g.get("_commission_sum") or 0.0) + float(c)
                        g["_has_commission"] = True
                except Exception:
                    pass

            # PnL: só realizado (SELL)
            try:
                if str(r.get("side") or "").lower() == "sell" and r.get("profit") is not None:
                    p = float(r.get("profit"))
                    g["profit"] = (float(g["profit"]) if g.get("profit") is not None else 0.0) + p
            except Exception:
                pass

            # Timestamp mais recente do grupo
            try:
                ts_r = float(r.get("timestamp")) if r.get("timestamp") is not None else None
                ts_g = float(g.get("timestamp")) if g.get("timestamp") is not None else None
                if ts_r is not None and (ts_g is None or ts_r > ts_g):
                    g["timestamp"] = ts_r
                    g["id"] = r.get("id")
            except Exception:
                pass

            # side preferir não-null (e manter coerência)
            if not g.get("side") and r.get("side"):
                g["side"] = r.get("side")

        out: List[Dict[str, Any]] = []
        for g in grouped.values():
            bots = sorted(list(g.pop("_bots", set())))
            strategies = sorted(list(g.pop("_strategies", set())))
            g["bot_id"] = ",".join(bots) if bots else g.get("bot_id")
            g["strategy"] = ",".join(strategies) if strategies else g.get("strategy")

            # Publish grouped fee
            try:
                has_c = bool(g.pop("_has_commission", False))
            except Exception:
                has_c = False
            try:
                csum = float(g.pop("_commission_sum", 0.0) or 0.0)
            except Exception:
                csum = 0.0
            g["commission"] = csum if has_c else None

            # Se não foi SELL, não mostrar profit como 0.0
            if str(g.get("side") or "").lower() != "sell":
                g["profit"] = None

            out.append(g)

        # rows já vêm em timestamp DESC, mas ao agrupar precisamos re-ordenar.
        try:
            out.sort(key=lambda x: float(x.get("timestamp") or 0.0), reverse=True)
        except Exception:
            pass
        return out

    
    # --- BOT SESSIONS ---
    
    def insert_bot_session(self, session_data: Dict[str, Any]) -> bool:
        """Insere uma nova sessão do bot"""
        def _do_insert_session(conn, data):
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO bot_sessions (
                    id, pid, symbol, mode, entry_price, targets,
                    trailing_stop_pct, stop_loss_pct, size, funds,
                    start_ts, status, executed_parts, remaining_fraction,
                    dry_run
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('id'),
                data.get('pid'),
                data.get('symbol'),
                data.get('mode'),
                data.get('entry_price'),
                json.dumps(data.get('targets', [])),
                data.get('trailing_stop_pct'),
                data.get('stop_loss_pct'),
                data.get('size'),
                data.get('funds'),
                data.get('start_ts', time.time()),
                'running',
                json.dumps([]),
                data.get('remaining_fraction', 1.0),
                1 if data.get('dry_run') else 0
            ))
            return True

        try:
            task = self.enqueue_write(_do_insert_session, session_data)
            task.wait()
            logger.info(f"Bot session created: {session_data.get('id')} (PID: {session_data.get('pid')})")
            return True
        except Exception as e:
            logger.error(f"Error inserting bot session: {e}")
            return False
    
    def update_bot_session(self, bot_id: str, updates: Dict[str, Any]) -> bool:
        """Atualiza a sessão do bot"""
        def _do_update_session(conn, bot_id, updates):
            cur = conn.cursor()
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [bot_id]
            cur.execute(f"UPDATE bot_sessions SET {set_clause} WHERE id = ?", values)
            return True

        try:
            task = self.enqueue_write(_do_update_session, bot_id, updates)
            return bool(task.wait())
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
    
    def add_equity_snapshot(self, balance_usdt: float, balances: dict = None, btc_price: float = None,
                           average_cost: float = None, num_positions: int = 0, bot_id: str = None) -> bool:
        """Adiciona um snapshot de patrimônio (equity)"""
        def _do_add_equity(conn, balance_usdt, balances_json, btc_price, average_cost, num_positions, bot_id):
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO equity_snapshots (timestamp, balance_usdt, balances, btc_price, average_cost, num_positions, bot_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (time.time(), balance_usdt, balances_json, btc_price, average_cost, num_positions, bot_id))
            return True

        try:
            balances_json = json.dumps(balances) if balances else None
            task = self.enqueue_write(_do_add_equity, balance_usdt, balances_json, btc_price, average_cost, num_positions, bot_id)
            res = bool(task.wait())
            if res:
                logger.info(f"Equity snapshot added: ${balance_usdt:,.2f}")
            return res
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
            result = []
            for row in rows:
                d = dict(row)
                if d.get('balances'):
                    try:
                        d['balances'] = json.loads(d['balances'])
                    except Exception:
                        d['balances'] = {}
                result.append(d)
            return result
        except Exception as e:
            logger.error(f"Error getting equity history: {e}")
            return []
    
    # --- BOT LOGS ---
    
    def add_bot_log(self, bot_id: str, level: str, message: str, 
                    data: Dict = None) -> bool:
        """Adiciona uma entrada de log do bot"""
        def _do_add_log(conn, bot_id, level, message, data_json):
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO bot_logs (bot_id, timestamp, level, message, data)
                VALUES (?, ?, ?, ?, ?)
            ''', (bot_id, time.time(), level, message, data_json))
            return cur.rowcount

        try:
            data_json = json.dumps(data) if data else None
            task = self.enqueue_write(_do_add_log, bot_id, level, message, data_json)
            task.wait()
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
        def _do_add_run(conn, bot_id, run_number, symbol, entry_price, total_targets):
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO eternal_runs 
                (bot_id, run_number, symbol, entry_price, total_targets, start_ts, status)
                VALUES (?, ?, ?, ?, ?, ?, 'running')
            ''', (bot_id, run_number, symbol, entry_price, total_targets, time.time()))
            return cur.lastrowid

        try:
            task = self.enqueue_write(_do_add_run, bot_id, run_number, symbol, entry_price, total_targets)
            run_id = task.wait()
            return int(run_id) if run_id is not None else -1
        except Exception as e:
            logger.error(f"Error adding eternal run: {e}")
            return -1
    
    def complete_eternal_run(self, run_id: int, exit_price: float, 
                             profit_pct: float, profit_usdt: float,
                             targets_hit: int) -> bool:
        """Finaliza um ciclo do eternal mode"""
        def _do_complete_run(conn, run_id, exit_price, profit_pct, profit_usdt, targets_hit):
            cur = conn.cursor()
            cur.execute('''
                UPDATE eternal_runs 
                SET exit_price = ?, profit_pct = ?, profit_usdt = ?,
                    targets_hit = ?, end_ts = ?, status = 'completed'
                WHERE id = ?
            ''', (exit_price, profit_pct, profit_usdt, targets_hit, time.time(), run_id))
            return cur.rowcount

        try:
            task = self.enqueue_write(_do_complete_run, run_id, exit_price, profit_pct, profit_usdt, targets_hit)
            return bool(task.wait())
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
        def _do_add_metric(conn, metric_name, metric_value, symbol):
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO risk_metrics (timestamp, metric_name, metric_value, symbol)
                VALUES (?, ?, ?, ?)
            ''', (time.time(), metric_name, metric_value, symbol))
            return cur.rowcount

        try:
            task = self.enqueue_write(_do_add_metric, metric_name, metric_value, symbol)
            task.wait()
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
            balances TEXT,
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

