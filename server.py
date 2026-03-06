#!/usr/bin/env python3
"""
Dev server for Tulsi's website.
Serves static files + POST /api/refresh triggers the newsletter crawler.

Usage: python3 server.py
"""
import http.server
import subprocess
import json
import sys
import os
from pathlib import Path

PORT     = 4321
BASE_DIR = Path(__file__).parent.resolve()


class WebsiteHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    # ── POST /api/refresh ─────────────────────────────────────────────────────
    def do_POST(self):
        if self.path == "/api/refresh":
            self._handle_refresh()
        else:
            self.send_error(404, "Not found")

    def _handle_refresh(self):
        self.log_message("🔄 /api/refresh — running newsletter crawler…")
        try:
            result = subprocess.run(
                [sys.executable, str(BASE_DIR / "fetch_newsletters.py")],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=120,
                stdin=subprocess.DEVNULL,   # prevent getpass from hanging
            )
            ok  = result.returncode == 0
            msg = (result.stdout + "\n" + result.stderr).strip()
            self.log_message("✅ Crawler done" if ok else f"❌ Crawler failed (exit {result.returncode})")
        except subprocess.TimeoutExpired:
            ok, msg = False, "Crawler timed out after 2 minutes."
            self.log_message("❌ Crawler timed out")
        except Exception as e:
            ok, msg = False, str(e)
            self.log_message("❌ Crawler error: %s", e)

        body = json.dumps({"ok": ok, "message": msg}).encode()
        self.send_response(200)
        self.send_header("Content-Type",   "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ── Quieter logs (suppress routine 200/304 for static files) ─────────────
    def log_message(self, format, *args):
        if len(args) >= 2 and args[1] in ("200", "304"):
            return   # skip noisy GET hits for .js/.css/fonts
        super().log_message(format, *args)


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    with http.server.HTTPServer(("", PORT), WebsiteHandler) as server:
        print(f"🌐  Website     →  http://localhost:{PORT}")
        print(f"📰  Newsletter  →  http://localhost:{PORT}/newsletter.html")
        print(f"🔄  Refresh API →  POST http://localhost:{PORT}/api/refresh")
        print("    Ctrl+C to stop.\n")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n👋  Server stopped.")
