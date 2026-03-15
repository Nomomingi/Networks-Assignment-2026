db:
	mysql -u root -p < schema.sql

seed:
	mysql -u root -p chat_app < seed.sql

requirements:
	pip3 install -r requirements.txt

env:
	echo "HOST=localhost\nPORT=3306\nDB_USER=root\nPASSWORD=\nDATABASE=chat_app\nNGROK_AUTHTOKEN=\nNGROK_AUTHTOKEN_P2P=" > .env

# ── Run targets ─────────────────────────────────────────────────────────────

# Start the Python TCP chat server
server:
	python3 Server.py

#
client:
	python3 Client.py


# ---- The ngrok tunnels are no longer used as before. They were used when we tried to implement a web based gui, but we switchted to terminal based gui. ---- IGNORE ---
# Start all three ngrok tunnels in one session (free-tier compatible).
# Requires ngrok v3 config at ~/Library/Application Support/ngrok/ngrok.yml
# Copy with:  cp ngrok.yml ~/Library/Application\ Support/ngrok/ngrok.yml
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
