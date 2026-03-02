db:
	mysql -u root -p < schema.sql

seed:
	mysql -u root -p chat_app < seed.sql

.phoney: seed db