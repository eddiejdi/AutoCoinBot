try:
    import streamlit.components.v1 as components
except Exception:
    components = None
import json
import base64
import threading
import socket
import http.server
import socketserver
from pathlib import Path
from typing import Optional
import urllib.parse
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


def render_terminal(log_content: str = "", height: int = 600, bot_id: str = None, poll_ms: int = 2000):
    """
    Simple terminal for logs. If `bot_id` is provided, will attempt to start
    the local API server and poll `/api/logs`. Otherwise, renders static
    content passed in `log_content`.
    """
    safe_logs_b64 = base64.b64encode((log_content or "").encode("utf-8")).decode("ascii")

    port = None
    if bot_id:
        port = _LOG_SERVER.get("port") if _LOG_SERVER.get("mode") == "api" else None
        if port is None:
            port = start_api_server(8765)

    bot_id_json = json.dumps(bot_id) if bot_id else "null"
    port_value = port if port else "null"

    html = r"""
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
            const botId = {bot_id_json};
            const port = {port_value};
            const apiUrl = (botId && port) ? `http://${{window.location.hostname}}:${{port}}/api/logs?bot=${{encodeURIComponent(botId)}}&limit=30` : null;
            let lastText = null;

            function getLineColor(line) {{
                const lower = line.toLowerCase();
                if (/(lucro|profit):\s*([\d.]+)%/i.test(line)) {{
                    const match = /(lucro|profit):\s*([\d.]+)%/i.exec(line);
                    if (match && parseFloat(match[2]) > 0) return "line-profit";
                }}
                if (/preju[ií]zo|loss|unrealized.*-|profit.*-/i.test(line) || /-([\d.]+)%/.test(line)) return "line-loss";
                if (/❌|erro|error|failed/.test(line)) return "line-error";
                if (/✅|sucesso|success|conclu[ií]do/.test(line)) return "line-success";
                if (/compra|buy|venda|sell|order/.test(line)) return "line-info";
                if (/⚠️|aviso|warning/.test(line)) return "line-warning";
                return "line-neutral";
            }}

            function renderLogs(text) {{
                if (text === null || text === undefined) return;
                if (text === lastText) return;
                lastText = text;
                container.innerHTML = "";
                text.split("\n").forEach(line => {{
                    if (!line.trim()) return;
                    const div = document.createElement("div");
                    div.className = "line " + getLineColor(line);
                    div.textContent = line;
                    container.appendChild(div);
                }});
                container.scrollTop = container.scrollHeight;
            }}

            function initialRender() {{
                try {{
                    const initialLogs = atob("{safe_logs_b64}");
                    renderLogs(initialLogs);
                }} catch (e) {{}}
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
    """.format(height=height, safe_logs_b64=safe_logs_b64, poll_ms=poll_ms)

    components.html(html, height=height, scrolling=True)


def render_terminal_live(filename: str, height: int = 600, poll_ms: int = 1500, server_port: int = 8765):
    """
    Render a terminal that fetches a static file served by a local HTTP server.
    """
    safe_filename = json.dumps(filename)
    html = r"""
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ margin:0; background:#0d1117; font-family: Consolas, monospace; }}
            .terminal {{ height:{height}px; background:#161b22; border-radius:8px; overflow:hidden; }}
            .header {{ background:#21262d; padding:10px; color:#8b949e; font-size:13px; }}
            .content {{ padding:12px; overflow-y:auto; color:#c9d1d9; font-size:13px; line-height:1.6; white-space:pre-wrap; }}
            .line {{ padding:1px 0; }}
        </style>
    </head>
    <body>
        <div class="terminal">
            <div class="header">🤖 KuCoin Trading Bot — Terminal</div>
            <div class="content" id="log"></div>
        </div>
        <script>
            const filename = {safe_filename};
            const url = `http://localhost:{server_port}/${{JSON.parse(filename)}}`;
            const container = document.getElementById("log");
            let lastText = null;

            async function fetchAndUpdate() {{
                try {{
                    const r = await fetch(url, {{ cache: "no-store" }});
                    if (!r.ok) return;
                    const text = await r.text();
                    if (text === lastText) return;
                    lastText = text;
                    container.textContent = text;
                    container.scrollTop = container.scrollHeight;
                }} catch (e) {{}}
            }}

            fetchAndUpdate();
            setInterval(fetchAndUpdate, {poll_ms});
        </script>
    </body>
    </html>
    """.format(height=height, server_port=server_port, poll_ms=poll_ms, safe_filename=safe_filename)

    components.html(html, height=height, scrolling=True)


def _find_free_port(preferred: int = 8765, max_tries: int = 20) -> Optional[int]:
    # Try to find a free port. First prefer loopback bind (127.0.0.1)
    # but if that fails, fall back to binding on 0.0.0.0 so containers
    # or other network namespaces can accept connections when appropriate.
    for p in range(preferred, preferred + max_tries):
        # try loopback first
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", p))
                return p
        except OSError:
            pass

        # try all interfaces
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("0.0.0.0", p))
                return p
        except OSError:
            continue
    return None


def start_log_server(directory: str | Path, preferred_port: int = 8765) -> Optional[int]:
    """Start a simple Threading HTTP server serving `directory` on localhost."""
    global _LOG_SERVER

    if _LOG_SERVER.get("port"):
        return _LOG_SERVER.get("port")

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
        httpd = socketserver.ThreadingTCPServer(("127.0.0.1", port), handler)
        httpd.allow_reuse_address = True

        def serve():
            try:
                httpd.serve_forever()
            except Exception:
                pass

        thread = threading.Thread(target=serve, daemon=True, name="log-server")
        thread.start()

        _LOG_SERVER.update({"thread": thread, "port": port, "httpd": httpd, "mode": "static"})
        return port
    except Exception:
        return None


def start_api_server(preferred_port: int = 8765) -> Optional[int]:
    """Start a small API server that returns logs from the database.

    Exposes GET /api/logs?bot=<bot_id>&limit=<n>
    Returns JSON array of log objects.
    """
    global _LOG_SERVER

    if _LOG_SERVER.get("port") and _LOG_SERVER.get("mode") == "api":
        return _LOG_SERVER["port"]

    # If a static server is running, shut it down first
    if _LOG_SERVER.get("httpd") and _LOG_SERVER.get("mode") == "static":
        try:
            _LOG_SERVER["httpd"].shutdown()
        except Exception:
            pass
        _LOG_SERVER.update({"httpd": None, "thread": None, "port": None, "mode": None})

    port = _find_free_port(preferred_port)
    if port is None:
        return None

    class APIHandler(http.server.BaseHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET')
            self.send_header('Access-Control-Allow-Headers', '*')
            super().end_headers()

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != '/api/logs':
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Not Found')
                return

            params = urllib.parse.parse_qs(parsed.query)
            bot_id = params.get('bot', [None])[0]
            try:
                limit = max(1, min(int(params.get('limit', [30])[0]), 30))
            except Exception:
                limit = 30

            if not bot_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Missing bot parameter')
                return

            try:
                db = DatabaseManager()
                logs = db.get_bot_logs(bot_id, limit=limit)
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
        httpd = socketserver.ThreadingTCPServer(("0.0.0.0", port), APIHandler)
        httpd.allow_reuse_address = True

        def serve():
            try:
                httpd.serve_forever()
            except Exception:
                pass

        thread = threading.Thread(target=serve, daemon=True, name="log-api-server")
        thread.start()

        _LOG_SERVER.update({"thread": thread, "port": port, "httpd": httpd, "mode": "api"})
        try:
            portfile = Path.cwd() / "logs" / "api_port.txt"
            portfile.parent.mkdir(parents=True, exist_ok=True)
            with open(portfile, "w", encoding="utf-8") as pf:
                pf.write(str(port))
        except Exception:
            pass
        # write debug success to workspace logs if possible
        try:
            logpath = Path.cwd() / "logs" / "terminal_component_debug.log"
            logpath.parent.mkdir(parents=True, exist_ok=True)
            with open(logpath, "a", encoding="utf-8") as fh:
                fh.write(f"[start_api_server] started on port {port}\n")
        except Exception:
            pass
        return port
    except Exception as e:
        try:
            import traceback
            logpath = Path.cwd() / "logs" / "terminal_component_debug.log"
            logpath.parent.mkdir(parents=True, exist_ok=True)
            with open(logpath, "a", encoding="utf-8") as fh:
                fh.write("[start_api_server] exception:\n")
                fh.write(traceback.format_exc())
                fh.write("\n---\n")
        except Exception:
            pass
        try:
            portfile = Path.cwd() / "logs" / "api_port.txt"
            if portfile.exists():
                portfile.unlink()
        except Exception:
            pass
        return None


def render_terminal_live_api(bot_id: str, height: int = 600, poll_ms: int = 1500, server_port: int = 8765):
    """Render a terminal that polls the local API server for logs."""
    if _LOG_SERVER.get('port') and _LOG_SERVER.get('mode') == 'api':
        port = _LOG_SERVER['port']
    else:
        port = start_api_server(server_port)

    if not port:
        # API not available — render a friendly static message instead of empty terminal
        html = r"""
        <div style="background:#161b22;color:#c9d1d9;padding:16px;border-radius:8px;">
            <h3 style="margin:0 0 8px 0;">Terminal (offline)</h3>
            <p style="margin:0">O serviço local de terminal (API) não está disponível. Verifique logs em <code>logs/terminal_component_debug.log</code> e execute o serviço via `scripts/run_service.sh api start --no-docker`.</p>
        </div>
        """
        if components:
            components.html(html, height=height, scrolling=True)
        else:
            try:
                print(html)
            except Exception:
                pass
        return

    safe_bot = json.dumps(bot_id)
    html = r"""
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
            let lastText = null;

            async function fetchAndRender() {{
                try {{
                    const r = await fetch(url, {{cache:'no-store'}});
                    if (!r.ok) return;
                    const logs = await r.json();
                    const text = logs.map(l => `[${{l.level}}] ${{l.message}}`).join("\n");
                    if (text === lastText) return;
                    lastText = text;
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
    """.format(height=height, port=port, poll_ms=poll_ms, safe_bot=safe_bot)

    components.html(html, height=height, scrolling=True)
# terminal_component.py
import streamlit.components.v1 as components
import json
import base64
import threading
import socket
import http.server
import socketserver
from pathlib import Path
from typing import Optional
import urllib.parse
from database import DatabaseManager
import json
# terminal_component.py
import streamlit.components.v1 as components
import json
import base64
import threading
import socket
import http.server
import socketserver
from pathlib import Path
from typing import Optional
import urllib.parse
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


def render_terminal(log_content: str = "", height: int = 600, bot_id: str = None, poll_ms: int = 2000):
    """
    Simple terminal for logs. If `bot_id` is provided, will attempt to start
    the local API server and poll `/api/logs`. Otherwise, renders static
    content passed in `log_content`.
    """
    safe_logs_b64 = base64.b64encode((log_content or "").encode("utf-8")).decode("ascii")

    port = None
    if bot_id:
        port = _LOG_SERVER.get("port") if _LOG_SERVER.get("mode") == "api" else None
        if port is None:
            port = start_api_server(8765)

    bot_id_json = json.dumps(bot_id) if bot_id else "null"
    port_value = port if port else "null"

    html = r"""
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
            const botId = {bot_id_json};
            const port = {port_value};
            const apiUrl = (botId && port) ? `http://${{window.location.hostname}}:${{port}}/api/logs?bot=${{encodeURIComponent(botId)}}&limit=30` : null;
            let lastText = null;

            function getLineColor(line) {{
                const lower = line.toLowerCase();
                if (/(lucro|profit):\s*([\d.]+)%/i.test(line)) {{
                    const match = /(lucro|profit):\s*([\d.]+)%/i.exec(line);
                    if (match && parseFloat(match[2]) > 0) return "line-profit";
                }}
                if (/preju[ií]zo|loss|unrealized.*-|profit.*-/i.test(line) || /-([\d.]+)%/.test(line)) return "line-loss";
                if (/❌|erro|error|failed/.test(line)) return "line-error";
                if (/✅|sucesso|success|conclu[ií]do/.test(line)) return "line-success";
                if (/compra|buy|venda|sell|order/.test(line)) return "line-info";
                if (/⚠️|aviso|warning/.test(line)) return "line-warning";
                return "line-neutral";
            }}

            function renderLogs(text) {{
                if (text === null || text === undefined) return;
                if (text === lastText) return;
                lastText = text;
                container.innerHTML = "";
                text.split("\n").forEach(line => {{
                    if (!line.trim()) return;
                    const div = document.createElement("div");
                    div.className = "line " + getLineColor(line);
                    div.textContent = line;
                    container.appendChild(div);
                }});
                container.scrollTop = container.scrollHeight;
            }}

            function initialRender() {{
                try {{
                    const initialLogs = atob("{safe_logs_b64}");
                    renderLogs(initialLogs);
                }} catch (e) {{}}
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
    """.format(height=height, safe_logs_b64=safe_logs_b64, poll_ms=poll_ms)

    components.html(html, height=height, scrolling=True)


def render_terminal_live(filename: str, height: int = 600, poll_ms: int = 1500, server_port: int = 8765):
    """
    Render a terminal that fetches a static file served by a local HTTP server.
    """
    safe_filename = json.dumps(filename)
    html = r"""
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ margin:0; background:#0d1117; font-family: Consolas, monospace; }}
            .terminal {{ height:{height}px; background:#161b22; border-radius:8px; overflow:hidden; }}
            .header {{ background:#21262d; padding:10px; color:#8b949e; font-size:13px; }}
            .content {{ padding:12px; overflow-y:auto; color:#c9d1d9; font-size:13px; line-height:1.6; white-space:pre-wrap; }}
            .line {{ padding:1px 0; }}
        </style>
    </head>
    <body>
        <div class="terminal">
            <div class="header">🤖 KuCoin Trading Bot — Terminal</div>
            <div class="content" id="log"></div>
        </div>
        <script>
            const filename = {safe_filename};
            const url = `http://localhost:{server_port}/${{JSON.parse(filename)}}`;
            const container = document.getElementById("log");
            let lastText = null;

            async function fetchAndUpdate() {{
                try {{
                    const r = await fetch(url, {{ cache: "no-store" }});
                    if (!r.ok) return;
                    const text = await r.text();
                    if (text === lastText) return;
                    lastText = text;
                    container.textContent = text;
                    container.scrollTop = container.scrollHeight;
                }} catch (e) {{}}
            }}

            fetchAndUpdate();
            setInterval(fetchAndUpdate, {poll_ms});
        </script>
    </body>
    </html>
    """.format(height=height, server_port=server_port, poll_ms=poll_ms, safe_filename=safe_filename)

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
    """Start a simple Threading HTTP server serving `directory` on localhost."""
    global _LOG_SERVER

    if _LOG_SERVER.get("port"):
        return _LOG_SERVER.get("port")

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
        httpd = socketserver.ThreadingTCPServer(("127.0.0.1", port), handler)
        httpd.allow_reuse_address = True

        def serve():
            try:
                httpd.serve_forever()
            except Exception:
                pass

        thread = threading.Thread(target=serve, daemon=True, name="log-server")
        thread.start()

        _LOG_SERVER.update({"thread": thread, "port": port, "httpd": httpd, "mode": "static"})
        return port
    except Exception:
        return None


def start_api_server(preferred_port: int = 8765) -> Optional[int]:
    """Start a small API server that returns logs from the database.

    Exposes GET /api/logs?bot=<bot_id>&limit=<n>
    Returns JSON array of log objects.
    """
    global _LOG_SERVER

    if _LOG_SERVER.get("port") and _LOG_SERVER.get("mode") == "api":
        return _LOG_SERVER["port"]

    # If a static server is running, shut it down first
    if _LOG_SERVER.get("httpd") and _LOG_SERVER.get("mode") == "static":
        try:
            _LOG_SERVER["httpd"].shutdown()
        except Exception:
            pass
        _LOG_SERVER.update({"httpd": None, "thread": None, "port": None, "mode": None})

    port = _find_free_port(preferred_port)
    if port is None:
        return None

    class APIHandler(http.server.BaseHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET')
            self.send_header('Access-Control-Allow-Headers', '*')
            super().end_headers()

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != '/api/logs':
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Not Found')
                return

            params = urllib.parse.parse_qs(parsed.query)
            bot_id = params.get('bot', [None])[0]
            try:
                limit = max(1, min(int(params.get('limit', [30])[0]), 30))
            except Exception:
                limit = 30

            if not bot_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Missing bot parameter')
                return

            try:
                db = DatabaseManager()
                logs = db.get_bot_logs(bot_id, limit=limit)
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
        httpd = socketserver.ThreadingTCPServer(("0.0.0.0", port), APIHandler)
        httpd.allow_reuse_address = True

        def serve():
            try:
                httpd.serve_forever()
            except Exception:
                pass

        thread = threading.Thread(target=serve, daemon=True, name="log-api-server")
        thread.start()

        _LOG_SERVER.update({"thread": thread, "port": port, "httpd": httpd, "mode": "api"})
        return port
    except Exception:
        return None


def render_terminal_live_api(bot_id: str, height: int = 600, poll_ms: int = 1500, server_port: int = 8765):
    """Render a terminal that polls the local API server for logs."""
    if _LOG_SERVER.get('port') and _LOG_SERVER.get('mode') == 'api':
        port = _LOG_SERVER['port']
    else:
        port = start_api_server(server_port)
    if not port:
        render_terminal('')
        return

    safe_bot = json.dumps(bot_id)
    html = r"""
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
            let lastText = null;

            async function fetchAndRender() {{
                try {{
                    const r = await fetch(url, {{cache:'no-store'}});
                    if (!r.ok) return;
                    const logs = await r.json();
                    const text = logs.map(l => `[${{l.level}}] ${{l.message}}`).join("\n");
                    if (text === lastText) return;
                    lastText = text;
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
    """.format(height=height, port=port, poll_ms=poll_ms, safe_bot=safe_bot)

    components.html(html, height=height, scrolling=True)
