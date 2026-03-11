db:
	mysql -u root -p < schema.sql

seed:
	mysql -u root -p chat_app < seed.sql

requirements:
	pip3 install -r requirements.txt

client-deps:
	cd client && npm install

env:
	echo "HOST=localhost\nPORT=3306\nDB_USER=root\nPASSWORD=\nDATABASE=chat_app\nNGROK_AUTHTOKEN=\nNGROK_AUTHTOKEN_P2P=" > .env

# ── Run targets ─────────────────────────────────────────────────────────────

# Start the Python TCP chat server
server:
	python3 Server.py

# Start the HTTP/WebSocket bridge (translates REST ↔ TCP)
bridge:
	python3 api_bridge.py

# Start the React web client (Vite dev server)
client:
	cd client && npm run dev

# Start all three ngrok tunnels in one session (free-tier compatible).
# Requires ~/.config/ngrok/ngrok.yml — copy ngrok.example.yml and fill in your token.
tunnel:
	ngrok start --all

# ── Convenience: run everything in parallel (macOS / Linux) ──────────────────
# Each process gets its own terminal pane. Requires iTerm2 / tmux optional.
# You can also just open 4 terminals and run the targets above individually.
run-all:
	make server & make bridge & make client & make tunnel

# ── Utilities ────────────────────────────────────────────────────────────────
free_server_port:
	lsof -i:14532 -t | xargs kill -9

free_bridge_port:
	lsof -i:8000 -t | xargs kill -9

.PHONY: db seed requirements client-deps env server bridge client tunnel run-all free_server_port free_bridge_port
