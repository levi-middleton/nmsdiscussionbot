-- Create main submission table
CREATE TABLE IF NOT EXISTS submissions
	(name text NOT NULL UNIQUE,
	 title text NOT NULL,
	 hot integer NOT NULL);
