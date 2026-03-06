db:
	mysql -u root -p < schema.sql

seed:
	mysql -u root -p chat_app < seed.sql

requirements:
	echo "mysql-connector-python\npython-dotenv" > requirements.txt && pip3 install -r requirements.txt

env:
	echo "HOST=localhost\nPORT=3306\nDB_USER=root\nPASSWORD=\nDATABASE=chat_app" > .env

server:
	python3 Server.py &\
	ngrok tcp 14532

.phoney: seed db server requirements env