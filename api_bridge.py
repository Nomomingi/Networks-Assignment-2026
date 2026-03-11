"""
api_bridge.py — asyncio bridge between the React frontend and the Python TCP server.

HTTP REST + WebSocket on the same port (default 8000).
Requires: pip install aiohttp

Endpoints:
    POST /api/login          { username, password }
    POST /api/signup         { username, password }
    GET  /api/contacts?user= 
    GET  /api/search?user=&q=
    POST /api/open-chat      { user, peer }   → chat history + marks chat open
    POST /api/close-chat     { user, peer }
    POST /api/message        { user, peer, text }
    POST /api/logout         { user }
    WS   /ws?user=           real-time INCOMING_PRIVATE push
"""

import asyncio
import json
import os
from aiohttp import web

TCP_HOST     = os.getenv("CHAT_SERVER_HOST", "127.0.0.1")
TCP_PORT     = int(os.getenv("CHAT_SERVER_PORT", "14532"))
BRIDGE_PORT  = int(os.getenv("BRIDGE_PORT", "8000"))
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "http://localhost:5173")

# ─── Session ──────────────────────────────────────────────────────────────────

class ChatSession:
    """
    Wraps one persistent asyncio TCP connection to the Python chat server.
    A background reader loop routes packets to:
      - response_queue : responses to commands we sent (CONTACTS, SEARCH, …)
      - push_queue     : unsolicited pushes (INCOMING_PRIVATE)
    """

    def __init__(self, username: str,
                 reader: asyncio.StreamReader,
                 writer: asyncio.StreamWriter):
        self.username = username
        self.reader   = reader
        self.writer   = writer
        self.response_queue: asyncio.Queue[str] = asyncio.Queue()
        self.push_queue:     asyncio.Queue[str] = asyncio.Queue()
        self._lock   = asyncio.Lock()     # serialize command→response cycles
        self._task:  asyncio.Task | None  = None

    def start(self):
        self._task = asyncio.create_task(self._reader_loop(), name=f"reader-{self.username}")

    async def _reader_loop(self):
        buf = ""
        try:
            while True:
                chunk = await self.reader.read(4096)
                if not chunk:
                    break
                buf += chunk.decode(errors="ignore")
                while "\n\n" in buf:
                    packet, buf = buf.split("\n\n", 1)
                    packet = packet.strip()
                    if not packet:
                        continue
                    if packet.startswith("INCOMING_PRIVATE"):
                        await self.push_queue.put(packet)
                    else:
                        await self.response_queue.put(packet)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[Bridge] Reader error for {self.username}: {e}")

    async def command(self, packet: str, timeout: float = 8.0) -> str:
        """Send a command and wait for the server's response (serialized)."""
        async with self._lock:
            self.writer.write(packet.encode())
            await self.writer.drain()
            try:
                return await asyncio.wait_for(self.response_queue.get(), timeout=timeout)
            except asyncio.TimeoutError:
                return "ERROR|TIMEOUT"

    async def close(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:
            pass


# ─── Session store ────────────────────────────────────────────────────────────

sessions: dict[str, ChatSession] = {}


async def _new_session(username: str, first_packet: str) -> tuple[ChatSession | None, str]:
    """
    Open a fresh TCP connection, send first_packet, return (session, response).
    Returns (None, error_str) on connection failure.
    """
    try:
        reader, writer = await asyncio.open_connection(TCP_HOST, TCP_PORT)
    except Exception as e:
        return None, f"Cannot reach chat server: {e}"

    sess = ChatSession(username, reader, writer)
    sess.start()
    resp = await sess.command(first_packet)
    return sess, resp


# ─── CORS helpers ─────────────────────────────────────────────────────────────

CORS = {
    "Access-Control-Allow-Origin":  ALLOWED_ORIGIN,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def ok_json(data: dict) -> web.Response:
    return web.Response(text=json.dumps(data), content_type="application/json",
                        status=200, headers=CORS)


def err_json(msg: str, status: int = 400) -> web.Response:
    return web.Response(text=json.dumps({"error": msg}), content_type="application/json",
                        status=status, headers=CORS)


def _session(username: str) -> ChatSession | None:
    return sessions.get(username)


def _require_session(username: str) -> ChatSession | web.Response:
    sess = sessions.get(username)
    if not sess:
        return err_json("Not logged in", 401)
    return sess


# ─── Route handlers ───────────────────────────────────────────────────────────

async def handle_options(req: web.Request) -> web.Response:
    return web.Response(status=200, headers=CORS)


async def handle_login(req: web.Request) -> web.Response:
    body = await req.json()
    u = (body.get("username") or "").strip()
    p = (body.get("password") or "").strip()
    if not u or not p:
        return err_json("Username and password required")

    # Close any existing session for this user
    old = sessions.pop(u, None)
    if old:
        await old.close()

    sess, resp = await _new_session(u, f"LOGIN\n{u}\n{p}\n\n")
    if sess is None:
        return err_json(resp, 502)

    MAP = {
        "OK|LOGIN_SUCCESS":          (200, {"username": u}),
        "ERROR|LOGIN_FAILED":        (401, {"error": "Incorrect username or password"}),
        "ERROR|INVALID_LOGIN_FORMAT":(400, {"error": "Invalid login format"}),
        "ERROR|DB_ERROR":            (503, {"error": "Server database error"}),
    }
    if resp in MAP:
        status, payload = MAP[resp]
        if status == 200:
            sessions[u] = sess
        else:
            await sess.close()
        return web.Response(text=json.dumps(payload), content_type="application/json",
                            status=status, headers=CORS)

    await sess.close()
    return err_json(f"Unexpected: {resp}", 500)


async def handle_signup(req: web.Request) -> web.Response:
    body = await req.json()
    u = (body.get("username") or "").strip()
    p = (body.get("password") or "").strip()
    if not u or not p:
        return err_json("Username and password required")

    old = sessions.pop(u, None)
    if old:
        await old.close()

    # CREATE + then immediately LOGIN so the user lands in online_users
    sess, resp = await _new_session(u, f"CREATE\n{u}\n{p}\n\n")
    if sess is None:
        return err_json(resp, 502)

    if resp == "OK|SIGNUP_SUCCESSFUL":
        # Now login on the same connection so they appear online
        resp2 = await sess.command(f"LOGIN\n{u}\n{p}\n\n")
        if resp2 == "OK|LOGIN_SUCCESS":
            sessions[u] = sess
            return ok_json({"username": u})
        await sess.close()
        return err_json("Created but could not log in automatically", 500)

    await sess.close()
    MAP = {
        "ERROR|USER_ALREADY_EXISTS": (409, "Username already taken"),
        "ERROR|INVALID_CREDENTIALS": (400, "Invalid credentials"),
        "ERROR|DB_ERROR":            (503, "Server database error"),
    }
    if resp in MAP:
        status, msg = MAP[resp]
        return err_json(msg, status)
    return err_json(f"Unexpected: {resp}", 500)


async def handle_logout(req: web.Request) -> web.Response:
    body = await req.json()
    u = (body.get("user") or "").strip()
    sess = sessions.pop(u, None)
    if sess:
        await sess.command(f"CLOSE\n\n")
        await sess.close()
    return ok_json({"ok": True})


async def handle_contacts(req: web.Request) -> web.Response:
    u = req.rel_url.query.get("user", "").strip()
    sess = _require_session(u)
    if isinstance(sess, web.Response):
        return sess

    resp = await sess.command("CONTACTS\n\n")
    lines = resp.split("\n")
    if lines[0] != "OK|CONTACTS":
        return err_json(f"Server error: {lines[0]}", 502)

    contacts = [l.strip() for l in lines[1:] if l.strip()]
    return ok_json({"contacts": contacts})


async def handle_search(req: web.Request) -> web.Response:
    u = req.rel_url.query.get("user", "").strip()
    q = req.rel_url.query.get("q", "").strip()
    sess = _require_session(u)
    if isinstance(sess, web.Response):
        return sess
    if not q:
        return ok_json({"results": []})

    resp = await sess.command(f"SEARCH\n{q}\n\n")
    lines = resp.split("\n")
    if lines[0] != "OK|SEARCH":
        return err_json(f"Server error: {lines[0]}", 502)

    results = [l.strip() for l in lines[1:] if l.strip()]
    return ok_json({"results": results})


async def handle_open_chat(req: web.Request) -> web.Response:
    body   = await req.json()
    u      = (body.get("user") or "").strip()
    peer   = (body.get("peer") or "").strip()
    sess = _require_session(u)
    if isinstance(sess, web.Response):
        return sess

    resp = await sess.command(f"OPEN_CHAT\n{peer}\n\n")
    lines = resp.split("\n")
    if lines[0] != "OK|CHAT_HISTORY":
        return err_json(f"Server error: {lines[0]}", 502)

    messages = []
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            messages.append({"sender": parts[0], "text": parts[1], "ts": parts[2]})

    return ok_json({"history": messages})


async def handle_close_chat(req: web.Request) -> web.Response:
    body = await req.json()
    u    = (body.get("user") or "").strip()
    peer = (body.get("peer") or "").strip()
    sess = _require_session(u)
    if isinstance(sess, web.Response):
        return sess

    await sess.command(f"CLOSE_CHAT\n{peer}\n\n")
    return ok_json({"ok": True})


async def handle_message(req: web.Request) -> web.Response:
    body = await req.json()
    u    = (body.get("user") or "").strip()
    peer = (body.get("peer") or "").strip()
    text = (body.get("text") or "").strip()
    sess = _require_session(u)
    if isinstance(sess, web.Response):
        return sess
    if not text:
        return err_json("Message text required")

    resp = await sess.command(f"PRIVATE\n{peer}\n{text}\n\n")
    if resp in ("OK|MESSAGE_SENT", "OK|PRIVATE_STORED"):
        return ok_json({"ok": True, "stored": resp == "OK|PRIVATE_STORED"})
    return err_json(f"Server error: {resp}", 502)


# ─── WebSocket ────────────────────────────────────────────────────────────────

async def handle_ws(req: web.Request) -> web.WebSocketResponse:
    u = req.rel_url.query.get("user", "").strip()
    sess = sessions.get(u)
    if not sess:
        raise web.HTTPForbidden(reason="Not logged in")

    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(req)
    print(f"[Bridge] WS connected for {u}")

    async def forward_pushes():
        while not ws.closed:
            try:
                packet = await asyncio.wait_for(sess.push_queue.get(), timeout=1.0)
                parts  = packet.split("\n")
                if parts[0] == "INCOMING_PRIVATE" and len(parts) >= 3:
                    await ws.send_str(json.dumps({
                        "type": "message",
                        "from": parts[1].strip(),
                        "text": parts[2].strip(),
                    }))
            except asyncio.TimeoutError:
                continue
            except Exception:
                break

    fwd = asyncio.create_task(forward_pushes())
    async for _ in ws:
        pass  # we only push; browser doesn't send over WS

    fwd.cancel()
    print(f"[Bridge] WS disconnected for {u}")
    return ws


# ─── App ──────────────────────────────────────────────────────────────────────

def build_app() -> web.Application:
    app = web.Application()

    # pre-flight for all routes
    app.router.add_route("OPTIONS", "/{path_info:.*}", handle_options)

    app.router.add_post("/api/login",      handle_login)
    app.router.add_post("/api/signup",     handle_signup)
    app.router.add_post("/api/logout",     handle_logout)
    app.router.add_get( "/api/contacts",   handle_contacts)
    app.router.add_get( "/api/search",     handle_search)
    app.router.add_post("/api/open-chat",  handle_open_chat)
    app.router.add_post("/api/close-chat", handle_close_chat)
    app.router.add_post("/api/message",    handle_message)
    app.router.add_get( "/ws",             handle_ws)

    return app


if __name__ == "__main__":
    print(f"[Bridge] http://localhost:{BRIDGE_PORT}  →  TCP {TCP_HOST}:{TCP_PORT}")
    web.run_app(build_app(), port=BRIDGE_PORT)
