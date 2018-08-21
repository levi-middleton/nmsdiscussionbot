-- remove user blacklist table
DROP TABLE IF EXISTS user_blacklist;

-- add user profile table
CREATE TABLE IF NOT EXISTS user_profile
	(username TEXT PRIMARY KEY,
	 date_added TEXT NOT NULL,
	 profile_level INTEGER NOT NULL,
	 is_blacklisted INTEGER NOT NULL);
