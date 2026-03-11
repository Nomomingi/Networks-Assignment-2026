# Networks Assignment — Group 81

**Team:** Paul Kabulu · Chandik Naidoo · Makolela Shibambu

A full-stack instant messaging application with a Python TCP backend, React web frontend, P2P file sharing, and real-time WebSocket messaging.

---

## Architecture Overview

```
React Web Client (Vite, port 5173)
        │  HTTP / WebSocket
        ▼
HTTP Bridge  (api_bridge.py, port 8000)
        │  raw TCP (custom protocol)
        ▼
Chat Server  (Server.py, port 14532)   ←→  MySQL DB
        │
        └──  P2P File Transfer (ngrok TCP tunnel, p2p.py)
```

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.11+ | |
| Node.js | 18+ | for the React client |
| MySQL | 8+ | must be running locally |
| ngrok | any | free account at ngrok.com |

---

## 1 — Database Setup

```bash
# Create the schema
make db

# (Optional) Populate with seed data
make seed
```

---

## 2 — Environment Variables

```bash
make env
```

This creates a `.env` file. Open it and fill in your values:

```ini
HOST=localhost
PORT=3306
DB_USER=root             # your MySQL username
PASSWORD=                # your MySQL password
DATABASE=chat_app
NGROK_AUTHTOKEN=         # from https://dashboard.ngrok.com/get-started/your-authtoken
NGROK_AUTHTOKEN_P2P=     # second ngrok account token (needed for P2P file transfer)
```

> **Why two ngrok tokens?** ngrok free accounts allow 1 simultaneous agent session. The main server uses one session; P2P file transfers need a separate session (second free account). Sign up at [ngrok.com](https://ngrok.com) with a different email for the second one.

---

## 3 — Python Dependencies

```bash
make requirements
```

---

## 4 — Node Dependencies

```bash
make client-deps
```

---

## 5 — ngrok Setup

Copy the example config to ngrok's default config location and fill in your authtoken:

```bash
# macOS / Linux
cp ngrok.example.yml ~/.config/ngrok/ngrok.yml
```

Then open `~/.config/ngrok/ngrok.yml` and replace `PASTE_YOUR_NGROK_AUTHTOKEN_HERE` with your token.

> **Free tier note:** `ngrok start --all` runs all 3 tunnels (TCP server + HTTP bridge + React client) in a **single agent session**, which is fully compatible with the free tier.

---

## 6 — Running the Application

Open **4 terminals** and run one command in each:

| Terminal | Command | What it does |
|---|---|---|
| 1 | `make server` | Python TCP chat server |
| 2 | `make bridge` | HTTP/WebSocket bridge |
| 3 | `make client` | React Vite dev server |
| 4 | `make tunnel` | All ngrok tunnels |

After `make tunnel` starts, ngrok will print something like:

```
Forwarding   tcp://0.tcp.eu.ngrok.io:12345  →  localhost:14532  (server)
Forwarding   https://abc-123.ngrok-free.app  →  localhost:8000   (bridge)
Forwarding   https://def-456.ngrok-free.app  →  localhost:5173   (client)
```

**Update `client/.env.local`** with the bridge's HTTPS URL before using the web client:

```ini
VITE_API_URL=https://abc-123.ngrok-free.app
VITE_WS_URL=wss://abc-123.ngrok-free.app/ws
```

Restart the Vite dev server (`make client`) so it picks up the new values.

**Share `https://def-456.ngrok-free.app`** with anyone who wants to use the app. They just open it in a browser — no setup required on their end.

> ngrok free tier shows a one-time interstitial page — click "Visit Site" to proceed.

---

## Testing Locally (no ngrok needed)

For local testing on the same machine, skip `make tunnel` and use the defaults:

```bash
make server   # terminal 1
make bridge   # terminal 2
make client   # terminal 3
```

Open [http://localhost:5173](http://localhost:5173) in your browser. Everything works locally; P2P file transfer will work on LAN but not across different networks.

---

## Features

- **Accounts** — create account / login
- **Private chat** — real-time messages via WebSocket push
- **Search users** — find anyone by username
- **File sharing** — P2P transfer via ngrok TCP tunnel (📎 button in chat)
  - Received files saved to `~/Downloads/group81/`
- **CLI client** — `python3 Client.py` for the original terminal interface

---

## Project Structure

```
.
├── Server.py          Python TCP server
├── Client.py          CLI client
├── Protocol.py        Message protocol constants
├── p2p.py             P2P file transfer (ngrok)
├── api_bridge.py      HTTP/WebSocket ↔ TCP bridge
├── db.py              MySQL helper
├── schema.sql         DB schema
├── seed.sql           Seed data
├── ngrok.example.yml  Copy to ~/.config/ngrok/ngrok.yml
├── Makefile           Run targets
└── client/            React web frontend (Vite + TypeScript)
    └── src/
        ├── pages/
        │   ├── login/
        │   ├── sign-up/
        │   └── home/      Main chat UI
        └── context/
            └── auth-context.tsx
```

---

## Acknowledgements

Generative AI (Claude, Gemini) was used to assist with:
- Fixing terminal input/output race conditions in the CLI client
- Implementing the HTTP bridge and WebSocket real-time layer
- Styling the React frontend