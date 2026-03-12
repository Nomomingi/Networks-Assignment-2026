import struct
import threading
import os

CHUNK_SIZE = 65_536  # 64 KB per chunk

# All received files land here; directory is created on first use.
SAVE_DIR = os.path.expanduser("~/Downloads/group81")


def receive_blob(host: str, port: int, filename: str) -> str | None:
    """
    Connects directly to the sender's TCP endpoint and saves the incoming
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