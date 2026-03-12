db:
	mysql -u root -p < schema.sql

seed:
	mysql -u root -p chat_app < seed.sql

requirements:
	pip3 install -r requirements.txt

client-deps:
	cd client && npm install

env:
	echo "HOST=localhost\nPORT=3306\nDB_USER=root\nPASSWORD=\nDATABASE=chat_app" > .env

# ── Run targets ─────────────────────────────────────────────────────────────

# Start the Python TCP chat server
server:
	python3 Server.py

# Start the HTTP/WebSocket bridge (translates REST ↔ TCP)
# Both bridge and server run on the Oracle machine; TCP_HOST defaults to 127.0.0.1
bridge:
	python3 api_bridge.py

# Start the React web client (Vite dev server — local dev only)
client:
	cd client && npm run dev

# ── Utilities ────────────────────────────────────────────────────────────────
free_server_port:
	lsof -i:14532 -t | xargs kill -9

free_bridge_port:
	lsof -i:8000 -t | xargs kill -9

.PHONY: db seed requirements client-deps env server bridge client free_server_port free_bridge_port
