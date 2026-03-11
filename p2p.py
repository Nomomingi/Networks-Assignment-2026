import struct
import threading
import os
import ngrok
from dotenv import load_dotenv

load_dotenv()  # make sure NGROK_AUTHTOKEN from .env is in the environment

CHUNK_SIZE = 65_536  # 64 KB per chunk

# All received files land here; directory is created on first use.
SAVE_DIR = os.path.expanduser("~/Downloads/group81")


def send_blob(file_path: str, clientSocket, my_username: str, peer_username: str) -> None:
    """
    Opens a temporary TCP listener on a free port, exposes it publicly via an
    ngrok TCP tunnel, then tells the main server to relay the public address to
    the recipient. The recipient connects directly to the ngrok URL — no data
    goes through the main server.

    Chunk protocol on the direct P2P connection:
        [4-byte big-endian length][data]  ...repeated...
        [4-byte 0x00000000]               <- EOF
    """
    if not os.path.isfile(file_path):
        print(f"[P2P] File not found: {file_path}")
        return

    filename = os.path.basename(file_path)

    # 1. Bind a local TCP listener on any free port
    from socket import socket as _socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
    listener = _socket(AF_INET, SOCK_STREAM)
    listener.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    listener.bind(("", 0))
    local_port = listener.getsockname()[1]
    listener.listen(1)

    # 2. Open an ngrok TCP tunnel to that local port.
    #    Use NGROK_AUTHTOKEN_P2P if set (a second account), otherwise fall back
    #    to NGROK_AUTHTOKEN.  The free tier allows only 1 session per account,
    #    so if the main server already occupies that session, a separate token
    #    is needed here.
    authtoken = os.getenv("NGROK_AUTHTOKEN_P2P") or os.getenv("NGROK_AUTHTOKEN")
    if not authtoken:
        print("[P2P] No ngrok authtoken found. Set NGROK_AUTHTOKEN_P2P in .env.")
        listener.close()
        return
    try:
        tunnel = ngrok.forward(local_port, proto="tcp", authtoken=authtoken)
    except Exception as e:
        print(f"[P2P] Could not open ngrok tunnel: {e}")
        listener.close()
        return

    # tunnel.url() → "tcp://X.tcp.ngrok.io:PORT"
    public_url = tunnel.url()          # e.g. "tcp://0.tcp.eu.ngrok.io:12345"
    host_port  = public_url.replace("tcp://", "")   # "0.tcp.eu.ngrok.io:12345"
    ngrok_host, ngrok_port = host_port.rsplit(":", 1)

    # 3. Tell the main server: "relay this address to peer_username"
    msg = f"SEND_BLOB\n{my_username}\n{peer_username}\n{filename}\n{ngrok_host}\n{ngrok_port}\n\n"
    clientSocket.sendall(msg.encode())
    print(f"[P2P] Tunnel open at {public_url}. Waiting for {peer_username}…")

    # 4. Stream the file to whoever connects (the recipient)
    def _stream():
        try:
            conn, addr = listener.accept()
            print(f"[P2P] Recipient connected. Sending '{filename}'…")
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    conn.sendall(struct.pack(">I", len(chunk)) + chunk)
            conn.sendall(struct.pack(">I", 0))  # EOF marker
            conn.close()
            print(f"[P2P] '{filename}' sent successfully.")
        except Exception as e:
            print(f"[P2P] Send error: {e}")
        finally:
            listener.close()
            ngrok.disconnect(public_url)   # close the tunnel when done

    threading.Thread(target=_stream, daemon=True).start()


def receive_blob(host: str, port: int, filename: str) -> str | None:
    """
    Connects directly to the sender's ngrok TCP tunnel and saves the incoming
    blob to ~/Downloads/group81/. Returns the full save path on success, None on error.
    """
    from socket import socket as _socket, AF_INET, SOCK_STREAM

    os.makedirs(SAVE_DIR, exist_ok=True)

    # Avoid overwriting existing files by appending a counter
    base, ext = os.path.splitext(filename)
    save_path = os.path.join(SAVE_DIR, filename)
    counter = 1
    while os.path.exists(save_path):
        save_path = os.path.join(SAVE_DIR, f"{base}_{counter}{ext}")
        counter += 1

    try:
        sock = _socket(AF_INET, SOCK_STREAM)
        sock.connect((host, port))
        print(f"\n[P2P] Connected to sender. Receiving '{filename}'…")
        with open(save_path, "wb") as f:
            while True:
                raw_len = _recv_exact(sock, 4)
                if raw_len is None:
                    print("[P2P] Connection closed unexpectedly.")
                    break
                chunk_len = struct.unpack(">I", raw_len)[0]
                if chunk_len == 0:
                    break  # EOF
                data = _recv_exact(sock, chunk_len)
                if data is None:
                    print("[P2P] Connection closed mid-transfer.")
                    break
                f.write(data)
        sock.close()
        print(f"[P2P] Saved: {save_path}")
        return save_path
    except Exception as e:
        print(f"[P2P] Receive error: {e}")
        return None


def _recv_exact(sock, n: int) -> bytes | None:
    """Read exactly n bytes from sock, or return None if the connection closes."""
    buf = b""
    while len(buf) < n:
        piece = sock.recv(n - len(buf))
        if not piece:
            return None
        buf += piece
    return buf