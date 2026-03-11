"""
api_bridge.py — HTTP bridge between the React frontend and the Python TCP server.

Exposes:
    POST /api/login   { "username": "...", "password": "..." }
    POST /api/signup  { "username": "...", "password": "..." }

Runs on http://localhost:8000 by default.
Set SERVER_HOST / SERVER_PORT env vars to point at a different TCP server.
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from socket import socket, AF_INET, SOCK_STREAM

# --- TCP server coordinates (default: local dev) ---
TCP_HOST = os.getenv("CHAT_SERVER_HOST", "127.0.0.1")
TCP_PORT = int(os.getenv("CHAT_SERVER_PORT", "14532"))
BRIDGE_PORT = int(os.getenv("BRIDGE_PORT", "8000"))
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "http://localhost:5173")


def tcp_request(packet: str) -> str:
    """Open a fresh TCP connection, send packet, read until \\n\\n, return response."""
    sock = socket(AF_INET, SOCK_STREAM)
    sock.settimeout(8)
    sock.connect((TCP_HOST, TCP_PORT))
    sock.sendall(packet.encode())

    data = ""
    while True:
        chunk = sock.recv(1024).decode(errors="ignore")
        if not chunk:
            break
        data += chunk
        if "\n\n" in data:
            break
    sock.close()
    return data.split("\n\n")[0].strip()


class BridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[Bridge] {fmt % args}")

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._json(400, {"error": "Invalid JSON"})
            return

        username = (data.get("username") or "").strip()
        password = (data.get("password") or "").strip()

        if not username or not password:
            self._json(400, {"error": "Username and password are required"})
            return

        if self.path == "/api/login":
            self._handle_login(username, password)
        elif self.path == "/api/signup":
            self._handle_signup(username, password)
        else:
            self._json(404, {"error": "Not found"})

    def _handle_login(self, username: str, password: str):
        try:
            response = tcp_request(f"LOGIN\n{username}\n{password}\n\n")
        except Exception as e:
            self._json(502, {"error": f"Could not reach chat server: {e}"})
            return

        if response == "OK|LOGIN_SUCCESS":
            self._json(200, {"username": username})
        elif response == "ERROR|LOGIN_FAILED":
            self._json(401, {"error": "Incorrect username or password"})
        elif response == "ERROR|INVALID_LOGIN_FORMAT":
            self._json(400, {"error": "Invalid login format"})
        elif response == "ERROR|DB_ERROR":
            self._json(503, {"error": "Server database error"})
        else:
            self._json(500, {"error": f"Unexpected server response: {response}"})

    def _handle_signup(self, username: str, password: str):
        try:
            response = tcp_request(f"CREATE\n{username}\n{password}\n\n")
        except Exception as e:
            self._json(502, {"error": f"Could not reach chat server: {e}"})
            return

        if response == "OK|SIGNUP_SUCCESSFUL":
            self._json(200, {"username": username})
        elif response == "ERROR|USER_ALREADY_EXISTS":
            self._json(409, {"error": "Username already taken"})
        elif response == "ERROR|INVALID_CREDENTIALS":
            self._json(400, {"error": "Invalid credentials"})
        elif response == "ERROR|INVALID_CREATE_FORMAT":
            self._json(400, {"error": "Invalid sign-up format"})
        elif response == "ERROR|DB_ERROR":
            self._json(503, {"error": "Server database error"})
        else:
            self._json(500, {"error": f"Unexpected server response: {response}"})

    def _json(self, status: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print(f"[Bridge] Listening on http://localhost:{BRIDGE_PORT}")
    print(f"[Bridge] Forwarding to TCP server at {TCP_HOST}:{TCP_PORT}")
    HTTPServer(("", BRIDGE_PORT), BridgeHandler).serve_forever()
