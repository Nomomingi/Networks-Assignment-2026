db:
	mysql -u root -p < schema.sql

seed:
	mysql -u root -p chat_app < seed.sql

requirements:
	echo "mysql-connector-python\npython-dotenv\nngrok" > requirements.txt && pip3 install -r requirements.txt

env:
	echo "HOST=localhost\nPORT=3306\nDB_USER=root # change this to your MySQL username\nPASSWORD= # use your MySQL password\nDATABASE=chat_app\nNGROK_AUTHTOKEN= "> .env

server:
	python3 Server.py &\
	ngrok tcp 14532

free_server_port:
	lsof -i:14532 -t | xargs kill -9

bridge:
	python3 api_bridge.py
client:
	cd client && npm i && npm run dev
.phoney: seed db server requirements env
