-- add user blacklist table
CREATE TABLE IF NOT EXISTS user_blacklist
	(username TEXT PRIMARY KEY,
	 date_added TEXT NOT NULL);
