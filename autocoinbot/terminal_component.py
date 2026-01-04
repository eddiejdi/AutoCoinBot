# terminal_component.py
import streamlit.components.v1 as components
import json
import base64
import threading
import time
import socket
import http.server
import socketserver
from pathlib import Path
from typing import Optional
import urllib.parse
try:
    from .database import DatabaseManager
    from .bot_controller import get_global_controller
except Exception:
    from database import DatabaseManager

try:
    from log_colorizer import LogColorizer
except ImportError:
    LogColorizer = None

# server state
_LOG_SERVER = {
    "thread": None,
    "port": None,
    "httpd": None,
    "mode": None,  # "api" or "static"
}

_LOG_SERVER_LOCK = threading.Lock()


class _ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


def render_terminal(log_content: str = "", height: int = 600, bot_id: str = None, poll_ms: int = 2000):
    """
    Terminal HTML simples para logs do bot. Mantém auto-scroll e colorização básica.
    Se `bot_id` for informado, faz polling da API local; caso contrário, usa conteúdo estático.
    """

    safe_logs_b64 = base64.b64encode(log_content.encode("utf-8")).decode("ascii")

    port = None
    if bot_id:
        port = _LOG_SERVER.get("port") if _LOG_SERVER.get("mode") == "api" else None
        if port is None:
            port = start_api_server(8765)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ margin:0; padding:0; background:#0d1117; font-family: Consolas, monospace; }}
            .terminal {{ display:flex; flex-direction:column; height:{height}px; background:#161b22; border-radius:8px; overflow:hidden; border:1px solid #30363d; }}
            .header {{ background:#21262d; padding:10px; color:#8b949e; font-size:12px; flex-shrink:0; border-bottom:1px solid #30363d; }}
            .content {{ padding:12px; overflow-y:auto; color:#c9d1d9; font-size:12px; line-height:1.5; white-space:pre-wrap; word-wrap:break-word; flex:1; }}
            .line {{ margin:0; padding:2px 0; }}
            .line-profit {{ color:#22c55e; font-weight:bold; }}
            .line-loss {{ color:#ef4444; font-weight:bold; }}
            .line-success {{ color:#22c55e; }}
            .line-error {{ color:#ef4444; font-weight:bold; }}
            .line-info {{ color:#06b6d4; }}
            .line-warning {{ color:#f59e0b; }}
            .line-neutral {{ color:#c9d1d9; }}
        </style>
    </head>
    <body>
        <div class="terminal">
            <div class="header">🤖 KuCoin Trading Bot — Terminal</div>
            <div class="content" id="log"></div>
        </div>

        <script>
            const container = document.getElementById("log");
            const botId = {json.dumps(bot_id) if bot_id else 'null'};
            const port = {port if port else 'null'};
            const apiUrl = (botId && port)
                ? `${{window.location.protocol}}//${{window.location.hostname}}:${{port}}/api/logs?bot=${{encodeURIComponent(botId)}}&limit=30`
                : null;
            let lastText = null;

            function getLineColor(line) {{
                const lower = line.toLowerCase();
                if (/(lucro|profit):\\s*([\\d.]+)%/i.test(line)) {{
                    const match = /(lucro|profit):\\s*([\\d.]+)%/i.exec(line);
                    if (match && parseFloat(match[2]) > 0) return "line-profit";
                }}
                if (/prejudizo|loss|unrealized.*-|profit.*-/i.test(line) || /-([\\d.]+)%/.test(line)) return "line-loss";
                if (/❌|erro|error|failed/.test(line)) return "line-error";
                if (/✅|sucesso|success|concluído/.test(line)) return "line-success";
                if (/compra|buy|venda|sell|order/.test(line)) return "line-info";
                if (/⚠️|aviso|warning/.test(line)) return "line-warning";
                return "line-neutral";
            }}

            function renderLogs(text) {{
                if (text === lastText) return;
                lastText = text;
                container.innerHTML = "";
                text.split("\n").forEach(line => {{
                    if (!line.trim()) return;
                    const div = document.createElement("div");
                    div.className = "line " + getLineColor(line);
                    div.textContent = line;
                    container.insertBefore(div, container.firstChild);
                }});
                container.scrollTop = container.scrollHeight;
            }}

            function initialRender() {{
                const initialLogs = atob("{safe_logs_b64}");
                renderLogs(initialLogs);
            }}

            async function pollApi() {{
                if (!apiUrl) return;
                try {{
                    const r = await fetch(apiUrl, {{ cache: "no-store" }});
                        if (!r.ok) return;
                        const logs = await r.json();
                        if (!Array.isArray(logs) || logs.length === 0) return;
                    const text = logs.map(l => `[${{l.level}}] ${{l.message}}`).join("\n");
                    renderLogs(text);
                }} catch (e) {{
                    // ignore fetch errors
                }}
            }}

            initialRender();
            if (apiUrl) {{
                pollApi();
                setInterval(pollApi, {poll_ms});
            }}
        </script>
    </body>
    </html>
    """

    components.html(html, height=height, scrolling=True)


def render_terminal_live(filename: str, height: int = 600, poll_ms: int = 1500, server_port: int = 8765):
    """Render a terminal that polls a local HTTP server for the given `filename`.

    The server must serve the `bot_logs` directory on the provided `server_port`.
    """
    safe_filename = json.dumps(filename)
    html = f"""
    <!doctype html>
    <html>
    <head>
        <meta charset=\"utf-8\">
        <style>
            body {{ margin:0; background:#0d1117; font-family: Consolas, monospace; }}
            .terminal {{ height:{height}px; background:#161b22; border-radius:8px; overflow:hidden; }}
            .header {{ background:#21262d; padding:10px; color:#8b949e; font-size:13px; }}
            .content {{ padding:12px; overflow-y:auto; color:#c9d1d9; font-size:13px; line-height:1.6; white-space:pre-wrap; }}
        </style>
    </head>
    <body>
        <div class=\"terminal\">
            <div class=\"header\">🤖 KuCoin Trading Bot — Terminal</div>
            <div class=\"content\" id=\"log\"></div>
        </div>
        <script>
            const filename = {safe_filename};
            const url = `http://localhost:{server_port}/${{filename}}`;
            const container = document.getElementById('log');
            let lastText = null;

            async function fetchAndUpdate() {{
                try {{
                    const r = await fetch(url, {{ cache: 'no-store' }});
                    if (!r.ok) return;
                    const text = await r.text();
                    if (text === lastText) return;
                    lastText = text;
                    container.textContent = text;
                    container.scrollTop = container.scrollHeight;
                }} catch (e) {{
                    // ignore network errors
                }}
            }}

            fetchAndUpdate();
            setInterval(fetchAndUpdate, {poll_ms});
        </script>
    </body>
    </html>
    """

    components.html(html, height=height, scrolling=True)


def _find_free_port(preferred: int = 8765, max_tries: int = 20) -> Optional[int]:
    for p in range(preferred, preferred + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return None


def start_log_server(directory: str | Path, preferred_port: int = 8765) -> Optional[int]:
    """Start a simple Threading HTTP server serving `directory` on localhost.

    Returns the port number if successful, otherwise None.
    Safe to call multiple times; will reuse existing server.
    """
    global _LOG_SERVER

    with _LOG_SERVER_LOCK:
        if _LOG_SERVER.get("port"):
            # If an API server is running, do not override it
            if _LOG_SERVER.get("mode") == "api":
                return _LOG_SERVER["port"]
            if _LOG_SERVER.get("mode") == "static":
                return _LOG_SERVER["port"]

    dir_path = str(directory)

    port = _find_free_port(preferred_port)
    if port is None:
        return None

    class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET')
            self.send_header('Access-Control-Allow-Headers', '*')
            super().end_headers()

    handler = lambda *args, directory=dir_path, **kwargs: CORSRequestHandler(*args, directory=directory, **kwargs)

    try:
        httpd = _ReusableThreadingTCPServer(("127.0.0.1", port), handler)

        def serve():
            try:
                httpd.serve_forever()
            except Exception:
                pass

        thread = threading.Thread(target=serve, daemon=True, name="log-server")
        thread.start()

        with _LOG_SERVER_LOCK:
            _LOG_SERVER["thread"] = thread
            _LOG_SERVER["port"] = port
            _LOG_SERVER["httpd"] = httpd
            _LOG_SERVER["mode"] = "static"

        return port
    except Exception:
        return None


def start_api_server(preferred_port: int = 8765) -> Optional[int]:
    """Start a small API server that returns logs from the database.

    Exposes GET /api/logs?bot=<bot_id>&limit=<n>
    Returns JSON array of log objects.
    """
    global _LOG_SERVER

    def _is_api_server_healthy(port: int) -> bool:
        try:
            p = int(port)
        except Exception:
            return False
        if p <= 0:
            return False
        try:
            # Use a stable endpoint for health-checking (avoid relying on HTML contents).
            with socket.create_connection(("127.0.0.1", p), timeout=0.35) as s:
                req = (
                    b"GET /api/logs?bot=__health__&limit=1 HTTP/1.0\r\n"
                    b"Host: 127.0.0.1\r\n"
                    b"Connection: close\r\n\r\n"
                )
                s.sendall(req)
                data = s.recv(4096)
            if not data:
                return False
            first = data.split(b"\r\n", 1)[0]
            return (b"200" in first) and (b"[" in data)
        except Exception:
            return False

    with _LOG_SERVER_LOCK:
        # Reuse only if an API server is already running AND healthy; otherwise start a new API server
        if _LOG_SERVER.get("port") and _LOG_SERVER.get("mode") == "api":
            try:
                existing_port = int(_LOG_SERVER["port"])
            except Exception:
                existing_port = None

            if existing_port and _is_api_server_healthy(existing_port):
                return existing_port

            # Stale or wrong server on that port: shutdown and restart
            try:
                if _LOG_SERVER.get("httpd"):
                    _LOG_SERVER["httpd"].shutdown()
            except Exception:
                pass
            _LOG_SERVER.update({"httpd": None, "thread": None, "port": None, "mode": None})

        # If a static server is running, shut it down to free the port space
        if _LOG_SERVER.get("httpd") and _LOG_SERVER.get("mode") == "static":
            try:
                _LOG_SERVER["httpd"].shutdown()
            except Exception:
                pass
            _LOG_SERVER.update({"httpd": None, "thread": None, "port": None, "mode": None})

        port = _find_free_port(preferred_port)
        if port is None:
            return None

    base_dir = Path(__file__).resolve().parent
    monitor_html_path = (base_dir / "monitor_window.html")
    report_html_path = (base_dir / "report_window.html")
    _monitor_cache_lock = threading.Lock()
    monitor_html_cache: dict[str, object] = {"mtime_ns": None, "bytes": None}
    _report_cache_lock = threading.Lock()
    report_html_cache: dict[str, object] = {"mtime_ns": None, "bytes": None}

    def get_monitor_html_bytes() -> bytes | None:
        try:
            if not monitor_html_path.exists():
                return None
            st = monitor_html_path.stat()
            mtime_ns = getattr(st, "st_mtime_ns", None)
            with _monitor_cache_lock:
                if (
                    monitor_html_cache.get("bytes") is None
                    or mtime_ns is None
                    or monitor_html_cache.get("mtime_ns") != mtime_ns
                ):
                    monitor_html_cache["bytes"] = monitor_html_path.read_bytes()
                    monitor_html_cache["mtime_ns"] = mtime_ns
                b = monitor_html_cache.get("bytes")
                return b if isinstance(b, (bytes, bytearray)) else None
        except Exception:
            return None

    def get_report_html_bytes() -> bytes | None:
        try:
            if not report_html_path.exists():
                return None
            st = report_html_path.stat()
            mtime_ns = getattr(st, "st_mtime_ns", None)
            with _report_cache_lock:
                if (
                    report_html_cache.get("bytes") is None
                    or mtime_ns is None
                    or report_html_cache.get("mtime_ns") != mtime_ns
                ):
                    report_html_cache["bytes"] = report_html_path.read_bytes()
                    report_html_cache["mtime_ns"] = mtime_ns
                b = report_html_cache.get("bytes")
                return b if isinstance(b, (bytes, bytearray)) else None
        except Exception:
            return None

    themes_dir = base_dir / "themes"

    class APIHandler(http.server.BaseHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')
            super().end_headers()

        def do_OPTIONS(self):
            self.send_response(204)
            self.end_headers()

        def _read_json_body(self) -> dict:
            try:
                ln = int(self.headers.get('Content-Length') or 0)
            except Exception:
                ln = 0
            if ln <= 0:
                return {}
            try:
                raw = self.rfile.read(ln)
            except Exception:
                return {}
            try:
                return json.loads(raw.decode('utf-8')) if raw else {}
            except Exception:
                return {}

        def _send_json(self, status: int, payload: dict):
            self.send_response(int(status))
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            try:
                self.wfile.write(json.dumps(payload, default=str).encode('utf-8'))
            except Exception:
                try:
                    self.wfile.write(b'{}')
                except Exception:
                    pass

        def do_POST(self):
            # Minimal control API used for frontend-driven smoke tests.
            # This server runs in-process with Streamlit (thread), so it can operate
            # on the shared BotController and write to the same DB.
            raw_path = self.path or ''
            parsed = urllib.parse.urlparse(raw_path)

            if parsed.path == '/api/start':
                body = self._read_json_body()
                try:
                    symbol = body.get('symbol') or 'BTC-USDT'
                    entry = float(body.get('entry') or 0.0)
                    mode = body.get('mode') or 'buy'
                    targets = body.get('targets') or '-5:0.5,-10:0.5'
                    interval = float(body.get('interval') or 5.0)
                    size = body.get('size')
                    funds = body.get('funds')
                    dry = bool(body.get('dry'))
                    reserve_pct = float(body.get('reserve_pct') or 50.0)
                    target_profit_pct = float(body.get('target_profit_pct') or 2.0)
                    eternal_mode = bool(body.get('eternal_mode'))

                    try:
                        size = float(size) if size is not None else None
                    except Exception:
                        size = None
                    try:
                        funds = float(funds) if funds is not None else 0.0
                    except Exception:
                        funds = 0.0

                    controller = get_global_controller()
                    bot_id = controller.start_bot(
                        symbol=symbol,
                        entry=entry,
                        mode=mode,
                        targets=str(targets),
                        interval=interval,
                        size=size if size is not None else 0.0,
                        funds=funds,
                        dry=dry,
                        reserve_pct=reserve_pct,
                        target_profit_pct=target_profit_pct,
                        eternal_mode=eternal_mode,
                    )
                    self._send_json(200, {'ok': True, 'bot_id': bot_id})
                except Exception as e:
                    self._send_json(400, {'ok': False, 'error': 'start_failed', 'message': str(e)})
                return

            if parsed.path == '/api/stop':
                body = self._read_json_body()
                bot_id = body.get('bot_id')
                if not bot_id:
                    self._send_json(400, {'ok': False, 'error': 'missing_bot_id'})
                    return
                try:
                    controller = get_global_controller()
                    try:
                        controller.stop_bot(str(bot_id))
                    except Exception:
                        pass

                    # best-effort: mark stopped + release quota
                    try:
                        db = DatabaseManager()
                        db.update_bot_session(str(bot_id), {'status': 'stopped', 'end_ts': time.time()})
                        try:
                            db.release_bot_quota(str(bot_id))
                        except Exception:
                            pass
                    except Exception:
                        pass

                    self._send_json(200, {'ok': True, 'bot_id': str(bot_id)})
                except Exception as e:
                    self._send_json(400, {'ok': False, 'error': 'stop_failed', 'message': str(e)})
                return

            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
            return

        def do_GET(self):
            # Backward-compatibility: some links were generated as "/report&k=v" (missing '?').
            # Convert "/report&..." and "/monitor&..." into proper query strings.
            raw_path = self.path or ''
            try:
                if raw_path.startswith('/report&'):
                    raw_path = '/report?' + raw_path.split('&', 1)[1]
                elif raw_path.startswith('/monitor&'):
                    raw_path = '/monitor?' + raw_path.split('&', 1)[1]
            except Exception:
                pass

            parsed = urllib.parse.urlparse(raw_path)

            # Static theme assets (user-provided). Example: /themes/<pack>/backgrounds/foo.png
            if parsed.path.startswith('/themes/'):
                try:
                    if not themes_dir.exists() or not themes_dir.is_dir():
                        self.send_response(404)
                        self.end_headers()
                        return

                    rel = parsed.path.lstrip('/')  # remove leading '/'
                    # Prevent traversal
                    candidate = (base_dir / rel).resolve()
                    if themes_dir not in candidate.parents and candidate != themes_dir:
                        self.send_response(403)
                        self.end_headers()
                        return
                    if not candidate.exists() or not candidate.is_file():
                        self.send_response(404)
                        self.end_headers()
                        return

                    ctype = 'application/octet-stream'
                    suf = candidate.suffix.lower()
                    if suf == '.png':
                        ctype = 'image/png'
                    elif suf in ('.jpg', '.jpeg'):
                        ctype = 'image/jpeg'
                    elif suf == '.webp':
                        ctype = 'image/webp'
                    elif suf == '.json':
                        ctype = 'application/json; charset=utf-8'
                    elif suf in ('.txt', '.md'):
                        ctype = 'text/plain; charset=utf-8'

                    data = candidate.read_bytes()
                    self.send_response(200)
                    self.send_header('Content-Type', ctype)
                    self.send_header('Cache-Control', 'no-store')
                    self.end_headers()
                    self.wfile.write(data)
                except Exception:
                    self.send_response(500)
                    self.end_headers()
                return

            if parsed.path in ('/monitor', '/monitor/'):
                monitor_html_bytes = get_monitor_html_bytes()
                if not monitor_html_bytes:
                    self.send_response(500)
                    self.send_header('Content-Type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(b'monitor_window.html not found')
                    return
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(monitor_html_bytes)
                return

            if parsed.path in ('/report', '/report/'):
                report_html_bytes = get_report_html_bytes()
                if not report_html_bytes:
                    self.send_response(500)
                    self.send_header('Content-Type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(b'report_window.html not found')
                    return
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(report_html_bytes)
                return

            if parsed.path == '/api/bot':
                params = urllib.parse.parse_qs(parsed.query)
                bot_id = params.get('bot', [None])[0]
                if not bot_id:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'Missing bot parameter')
                    return
                try:
                    db = DatabaseManager()
                    conn = db.get_connection()
                    cur = conn.cursor()
                    cur.execute('SELECT * FROM bot_sessions WHERE id = ? LIMIT 1', (bot_id,))
                    row = cur.fetchone()
                    conn.close()

                    if not row:
                        self.send_response(404)
                        self.send_header('Content-Type', 'application/json; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(json.dumps({'error': 'bot_not_found', 'bot_id': bot_id}).encode('utf-8'))
                        return

                    payload = dict(row)
                    # best-effort decode of JSON fields
                    for k in ('targets', 'executed_parts', 'metadata'):
                        if k in payload and isinstance(payload[k], str) and payload[k]:
                            try:
                                payload[k] = json.loads(payload[k])
                            except Exception:
                                pass

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps(payload, default=str).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(str(e).encode('utf-8'))
                return

            if parsed.path == '/api/trades':
                params = urllib.parse.parse_qs(parsed.query)
                bot_id = params.get('bot', [None])[0]
                only_real_raw = params.get('only_real', [None])[0]
                group_raw = params.get('group', [None])[0]
                limit_raw = params.get('limit', [2000])[0]
                only_real = str(only_real_raw).strip().lower() in ('1', 'true', 'yes', 'y', 'on')
                group_by_order = True
                try:
                    if group_raw is not None and str(group_raw).strip().lower() in ('0', 'false', 'no', 'n', 'off'):
                        group_by_order = False
                except Exception:
                    group_by_order = True
                try:
                    limit = int(limit_raw)
                except Exception:
                    limit = 2000
                limit = max(1, min(limit, 5000))

                try:
                    db = DatabaseManager()
                    if group_by_order:
                        rows = db.get_trade_history_grouped(
                            limit=limit,
                            bot_id=bot_id,
                            only_real=only_real,
                            group_by_order_id=True,
                        )
                    else:
                        rows = db.get_trade_history(limit=limit, bot_id=bot_id, only_real=only_real)
                    if not isinstance(rows, list):
                        rows = []
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.send_header('Cache-Control', 'no-store')
                    self.end_headers()
                    self.wfile.write(json.dumps(rows, default=str).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'server_error', 'message': str(e)}).encode('utf-8'))
                return

            if parsed.path == '/api/equity/history':
                # Returns equity history for the chart
                try:
                    db = DatabaseManager()
                    rows = db.get_equity_history(days=30)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.send_header('Cache-Control', 'no-store')
                    self.end_headers()
                    self.wfile.write(json.dumps({'rows': rows}, default=str).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'server_error', 'message': str(e)}).encode('utf-8'))
                return

            if parsed.path == '/api/learning/symbols':
                try:
                    db = DatabaseManager()
                    symbols = []
                    try:
                        symbols = db.get_learning_symbols()
                    except Exception:
                        symbols = []
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.send_header('Cache-Control', 'no-store')
                    self.end_headers()
                    self.wfile.write(json.dumps({'symbols': symbols}, default=str).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'server_error', 'message': str(e)}).encode('utf-8'))
                return

            if parsed.path == '/api/learning/stats':
                params = urllib.parse.parse_qs(parsed.query)
                symbol = params.get('symbol', [None])[0]
                param = params.get('param', ['take_profit_trailing_pct'])[0]
                try:
                    db = DatabaseManager()
                    if not symbol:
                        # First-load UX: pick the first symbol if available, otherwise return empty.
                        try:
                            syms = db.get_learning_symbols() or []
                        except Exception:
                            syms = []
                        symbol = syms[0] if syms else None
                    rows = db.get_learning_stats(str(symbol), str(param)) if symbol else []
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.send_header('Cache-Control', 'no-store')
                    self.end_headers()
                    self.wfile.write(json.dumps({'rows': rows, 'symbol': symbol, 'param': param}, default=str).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'server_error', 'message': str(e)}).encode('utf-8'))
                return

            if parsed.path == '/api/learning/history':
                params = urllib.parse.parse_qs(parsed.query)
                symbol = params.get('symbol', [None])[0]
                param = params.get('param', ['take_profit_trailing_pct'])[0]
                limit_raw = params.get('limit', [2000])[0]
                try:
                    limit = int(limit_raw)
                except Exception:
                    limit = 2000
                limit = max(1, min(limit, 5000))
                try:
                    db = DatabaseManager()
                    if not symbol:
                        try:
                            syms = db.get_learning_symbols() or []
                        except Exception:
                            syms = []
                        symbol = syms[0] if syms else None
                    rows = db.get_learning_history(str(symbol), str(param), limit=limit) if symbol else []
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.send_header('Cache-Control', 'no-store')
                    self.end_headers()
                    self.wfile.write(json.dumps({'rows': rows, 'symbol': symbol, 'param': param}, default=str).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'server_error', 'message': str(e)}).encode('utf-8'))
                return

            if parsed.path == '/api/active_bot':
                try:
                    db = DatabaseManager()
                    # Get the most recent active bot
                    conn = db.get_connection()
                    cur = conn.cursor()
                    cur.execute('SELECT id FROM bot_sessions WHERE status = "running" ORDER BY start_ts DESC LIMIT 1', ())
                    row = cur.fetchone()
                    conn.close()
                    if row:
                        bot_id = row[0]
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(json.dumps({'bot_id': bot_id}, default=str).encode('utf-8'))
                    else:
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(json.dumps({'bot_id': None}, default=str).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'server_error', 'message': str(e)}).encode('utf-8'))
                return

            if parsed.path == '/api/debug/database_url':
                # TEMPORARY DIAGNOSTIC ENDPOINT - Remove after debugging
                try:
                    import os
                    database_url = os.environ.get("DATABASE_URL") or os.environ.get("TRADES_DB")
                    
                    if not database_url:
                        result = {"error": "DATABASE_URL not defined"}
                    else:
                        # Mask password
                        safe_url = database_url
                        if '@' in safe_url and ':' in safe_url:
                            parts = safe_url.split('@')
                            if len(parts) == 2:
                                before_at = parts[0]
                                if '://' in before_at:
                                    protocol, user_pass = before_at.split('://', 1)
                                    if ':' in user_pass:
                                        user, _ = user_pass.split(':', 1)
                                        safe_url = f"{protocol}://{user}:***@{parts[1]}"
                        
                        errors = []
                        if not database_url.startswith(('postgresql://', 'postgres://')):
                            errors.append("Must start with 'postgresql://' or 'postgres://'")
                        if '@' not in database_url:
                            errors.append("Missing '@' (host separator)")
                        if database_url.count(':') < 2:
                            errors.append("Missing ':' (separators)")
                        
                        # Check for space instead of '/' before database name
                        if '@' in database_url:
                            after_at = database_url.split('@')[1]
                            if ' ' in after_at and '/' not in after_at.split(' ')[0]:
                                errors.append("CRITICAL: Space instead of '/' before database name")
                                idx = after_at.index(' ')
                                errors.append(f"Found: '{after_at[max(0,idx-10):idx+20]}'")
                                errors.append("Expected format: 'host:port/database' not 'host:port database'")
                        
                        result = {
                            "url_safe": safe_url,
                            "length": len(database_url),
                            "has_space": ' ' in database_url,
                            "has_equals": '=' in database_url,
                            "format_errors": errors
                        }
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.send_header('Cache-Control', 'no-store')
                    self.end_headers()
                    self.wfile.write(json.dumps(result, default=str).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'server_error', 'message': str(e)}).encode('utf-8'))
                return

            if parsed.path != '/api/logs':
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Not Found')
                return

            params = urllib.parse.parse_qs(parsed.query)
            bot_id = params.get('bot', [None])[0]
            limit = max(1, min(int(params.get('limit', [30])[0]), 30))

            if not bot_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Missing bot parameter')
                return

            # Health check
            if bot_id == '__health__':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(b'[]')
                return

            try:
                db = DatabaseManager()
                logs = db.get_bot_logs(bot_id, limit=limit)
                # convert database rows/dicts to plain objects
                payload = json.dumps(logs, default=str)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(payload.encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))

    try:
        httpd = _ReusableThreadingTCPServer(("0.0.0.0", port), APIHandler)

        def serve():
            try:
                httpd.serve_forever()
            except Exception:
                pass

        thread = threading.Thread(target=serve, daemon=True, name="log-api-server")
        thread.start()

        with _LOG_SERVER_LOCK:
            _LOG_SERVER["thread"] = thread
            _LOG_SERVER["port"] = port
            _LOG_SERVER["httpd"] = httpd
            _LOG_SERVER["mode"] = "api"

        return port
    except Exception:
        return None


def render_terminal_live_api(bot_id: str, height: int = 600, poll_ms: int = 1500, server_port: int = 8765):
    """Render a terminal that polls the local API server for logs.

    The API server must be started with `start_api_server()`; this helper
    will attempt to start it automatically on `server_port`.
    """
    # Ensure we only reuse the port when an API server is actually running
    if _LOG_SERVER.get('port') and _LOG_SERVER.get('mode') == 'api':
        port = _LOG_SERVER['port']
    else:
        port = start_api_server(server_port)
    if not port:
        # fallback to static render
        render_terminal('')
        return

    safe_bot = json.dumps(bot_id)
    html = f"""
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ margin:0; background:#0d1117; font-family: Consolas, monospace; }}
            .terminal {{ height:{height}px; background:#161b22; border-radius:8px; overflow:hidden; display:flex; flex-direction:column }}
            .header {{ background:#21262d; padding:10px; color:#8b949e; font-size:13px; flex-shrink:0 }}
            .content {{ padding:12px; overflow-y:auto; color:#c9d1d9; font-size:13px; line-height:1.6; white-space:pre-wrap; flex:1 }}
            .line {{ padding:1px 0; }}
        </style>
    </head>
    <body>
        <div class="terminal">
            <div class="header">🤖 KuCoin Trading Bot — Terminal (Live)</div>
            <div class="content" id="log"></div>
        </div>
        <script>
            const bot = {safe_bot};
            const url = `${{window.location.protocol}}//${{window.location.hostname}}:{port}/api/logs?bot=${{encodeURIComponent(bot)}}&limit=30`;
            const container = document.getElementById('log');
            let lastLen = 0;

            async function fetchAndRender() {{
                try {{
                    const r = await fetch(url, {{cache:'no-store'}});
                    if (!r.ok) return;
                    const logs = await r.json();
                    const text = logs.map(l => `[${{l.level}}] ${{l.message}}`).join("\n");
                    if (text.length === lastLen) return;
                    lastLen = text.length;
                    container.innerHTML = '';
                    text.split('\n').forEach(line => {{ if(line.trim()) {{ const d = document.createElement('div'); d.className='line'; d.textContent=line; container.appendChild(d); }} }});
                    container.scrollTop = container.scrollHeight;
                }} catch(e) {{
                    // ignore
                }}
            }}

            fetchAndRender();
            setInterval(fetchAndRender, {poll_ms});
        </script>
    </body>
    </html>
    """

    components.html(html, height=height, scrolling=True)
