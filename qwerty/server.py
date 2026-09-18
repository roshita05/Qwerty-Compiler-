"""Local-only browser playground. Not a production or hostile-code sandbox."""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import multiprocessing
from pathlib import Path
import secrets
from urllib.parse import urlsplit
from .builtins import REGISTRY
from .compiler import compile_source
from .context import Context
from .errors import QwertyError
from .vm import VirtualMachine

WEB_ROOT = Path(__file__).resolve().parent.parent / "web"


def _worker(sender, action: str, source: str, input_text: str) -> None:
    # A best-effort extra POSIX guard. Windows has no equivalent here; for public
    # deployment use OS/container memory quotas and a separately secured service.
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
    except (ImportError, OSError, ValueError):
        pass
    context = None
    try:
        program = compile_source(source, "playground.qw")
        listing = program.disassemble()
        if len(listing) > 200_000:
            listing = listing[:200_000] + "\n... editor listing truncated; use the CLI for the full listing."
        payload = {"ok": True, "bytecode": listing, "steps": 0, "output": "", "action": action}
        if action == "run":
            context = Context(inputs=input_text.splitlines())
            result = VirtualMachine(program, context).run()
            payload.update(output=result.output, steps=result.steps)
    except QwertyError as error:
        payload = {"ok": False, "error": error.as_dict(),
                   "output": "".join(context.output) if context else "", "action": action}
    except (MemoryError, RecursionError):
        payload = {"ok": False, "error": {"formatted": "LimitError: worker resource limit reached."}, "output": ""}
    except Exception:
        # Do not leak Python tracebacks or local paths through the browser endpoint.
        payload = {"ok": False, "error": {"formatted": "InternalError: unexpected compiler failure. Run the tests or reproduce with the CLI."}, "output": ""}
    try:
        sender.send_bytes(json.dumps(payload, ensure_ascii=True).encode("utf-8"))
    finally:
        sender.close()


def run_isolated(action: str, source: str, input_text: str) -> dict:
    spawn = multiprocessing.get_context("spawn")
    receiver, sender = spawn.Pipe(duplex=False)
    worker = spawn.Process(target=_worker, args=(sender, action, source, input_text), daemon=True)
    worker.start()
    sender.close()
    try:
        if receiver.poll(6.0):
            try:
                return json.loads(receiver.recv_bytes(maxlength=2_000_000))
            except (EOFError, OSError, ValueError):
                return {"ok": False, "error": {"formatted": "LimitError: worker ended without a valid result."}, "output": ""}
        return {"ok": False, "error": {"formatted": "LimitError: execution worker exceeded the 6-second wall-clock limit."}, "output": ""}
    finally:
        receiver.close()
        worker.join(timeout=0.2)
        if worker.is_alive():
            worker.terminate()
            worker.join(timeout=1)
        if worker.is_alive():
            worker.kill()
            worker.join(timeout=1)
        worker.close()


class LocalServer(HTTPServer):
    def __init__(self, port: int):
        self.token = secrets.token_urlsafe(32)
        super().__init__(("127.0.0.1", port), Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = "QWERTYLocal/1.0"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(8)

    def log_message(self, format, *args):
        # Avoid echoing untrusted request data to the terminal.
        pass

    def response(self, status: int, body: bytes, content_type="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def json_response(self, status: int, data: dict):
        self.response(status, json.dumps(data, ensure_ascii=True).encode("utf-8"))

    def allowed_host(self) -> bool:
        allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        if self.headers.get("Host") not in allowed:
            self.json_response(403, {"error": "This editor accepts only its local host address."})
            return False
        return True

    def do_GET(self):
        if not self.allowed_host():
            return
        path = urlsplit(self.path).path
        if path == "/api/functions":
            self.json_response(200, {"functions": [{"name": f.name, "signature": f.signature,
                "category": f.category, "description": f.description, "example": f.example}
                for f in REGISTRY.values()]})
            return
        assets = {"/": ("index.html", "text/html; charset=utf-8"),
                  "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                  "/style.css": ("style.css", "text/css; charset=utf-8")}
        if path not in assets:
            self.json_response(404, {"error": "Not found."})
            return
        filename, content_type = assets[path]
        body = (WEB_ROOT / filename).read_bytes()
        if path == "/":
            body = body.replace(b"__QWERTY_TOKEN__", self.server.token.encode("ascii"))
        self.response(200, body, content_type)

    def do_POST(self):
        if not self.allowed_host():
            return
        allowed_origins = {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}
        if (self.headers.get("Origin") not in allowed_origins
                or not secrets.compare_digest(self.headers.get("X-Qwerty-Token", "").encode("utf-8"), self.server.token.encode("ascii"))):
            self.json_response(403, {"error": "Open the editor on localhost and try again."})
            return
        if urlsplit(self.path).path != "/api/execute":
            self.json_response(404, {"error": "Not found."})
            return
        try:
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                raise ValueError("Expected an application/json request.")
            length = int(self.headers.get("Content-Length", "-1"))
            if not 0 <= length <= 500_000:
                raise ValueError("Request body is missing or too large.")
            payload = json.loads(self.rfile.read(length))
            if type(payload) is not dict:
                raise ValueError("Expected a JSON object.")
            source, input_text, action = payload.get("source"), payload.get("input", ""), payload.get("action", "run")
            if type(source) is not str or len(source) > 100_000:
                raise ValueError("Source must be text with at most 100,000 characters.")
            if type(input_text) is not str or len(input_text) > 100_000:
                raise ValueError("Program input must be text with at most 100,000 characters.")
            if action not in ("run", "check"):
                raise ValueError("Action must be run or check.")
        except (ValueError, TypeError, UnicodeError) as error:
            self.json_response(400, {"error": str(error)})
            return
        self.json_response(200, run_isolated(action, source, input_text))


def serve(port=8765):
    if not 1 <= port <= 65_535:
        raise ValueError("Port must be between 1 and 65535.")
    server = LocalServer(port)
    print(f"QWERTY Studio: http://127.0.0.1:{port}", flush=True)
    print("Local use only. Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEditor stopped.")
    finally:
        server.server_close()
