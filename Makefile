db:
	mysql -u root -p < schema.sql

seed:
	mysql -u root -p chat_app < seed.sql

rquirements:
	pip install -r requirements.txt

.phoney: seed db