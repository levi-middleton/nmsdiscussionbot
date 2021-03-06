import praw
from pprint import pprint
import sqlite3
import logging.config
import json
import os
import datetime

def init_database():
	conn = sqlite3.connect('db.sqlite')
	conn.execute('CREATE TABLE IF NOT EXISTS migrations (filename TEXT PRIMARY KEY, run_date TEXT NOT NULL)')
	db = conn.cursor()
	for filename in sorted(os.listdir('migrations'),key=lambda f: int(''.join(filter(str.isdigit, f)))):
		if(not filename.endswith('.sql')):
			continue
		db.execute('SELECT COUNT(*) FROM migrations where filename = ?',(filename,))
		(number_of_rows,) = db.fetchone()
		if(number_of_rows != 0):
			continue
		logging.info('Running migration ' + filename)
		with open(os.path.join('migrations',filename)) as f:
			conn.executescript(f.read())
		conn.execute('INSERT INTO migrations (filename, run_date) VALUES (?,?)',(filename, str(datetime.datetime.now())))
	return conn

def is_good_submission(submission):
	if(submission.num_comments < 15):
		return False

	if (hasattr(submission,'link_flair_text') 
		and (('Information' in str(submission.link_flair_text).title()) 
			or ('Discussion' in str(submission.link_flair_text).title()))):
		return True

	if(submission.is_self):
		return True

	return False

def can_autoapprove_submission(submission):
	if(not is_good_submission(submission)):
		return False

	if(hasattr(submission,'post_hint') or submission.score < 5):
		return False

	return True

def get_flair_text(submission):
	if hasattr(submission,'link_flair_text'):
		if('Discussion' in str(submission.link_flair_text).title()):
			return 'Discussion'
		if('Suggestion' in str(submission.link_flair_text).title()):
			return 'Suggestion'
	return 'Information'

def crosspost_good_submissions(r, db):
	db.execute('UPDATE submissions SET hot = 0')
	crosspost_count = 0
	for submission in r.subreddit('nomansskythegame').hot(limit=1000):
		if is_good_submission(submission):
			db.execute('SELECT COUNT(*) FROM submissions WHERE name = ?',(str(submission.name),))
			(number_of_rows,) = db.fetchone()
			if(number_of_rows != 0):
				db.execute('UPDATE submissions SET hot = 1 WHERE name = ?',(str(submission.name),))
				continue
			has_crossposts = submission.num_crossposts != 0
			new_submission = submission.crosspost(subreddit="NMS_Discussions", send_replies=False)
			db.execute('INSERT INTO submissions(name,title,hot) VALUES (?,?,1)', (str(submission.name),str(submission.title)))
			new_submission.mod.lock()
			new_submission.mod.flair(text=get_flair_text(submission))
			if(can_autoapprove_submission(submission)):
				new_submission.mod.approve()
			logging.debug('Submitted new crosspost: ' + str(submission.title))
			crosspost_count += 1
	logging.info('Added ' + str(crosspost_count) + ' new crossposts.')
	db.execute('DELETE FROM submissions WHERE hot = 0')
	logging.info('Deleted ' + str(db.rowcount) + ' rows from crosspost cache.')

class objectview(object):
    def __init__(self, d):
        self.__dict__ = d

def check_unmoderated_items(r):
	for crosspost_submission in r.subreddit('NMS_Discussions').mod.unmoderated():
		if(not hasattr(crosspost_submission,'crosspost_parent_list')):
			continue
		submission = objectview(crosspost_submission.crosspost_parent_list[0])
		if(can_autoapprove_submission(submission)):
			crosspost_submission.mod.approve()

def respond_to_inbox(r, db):
	for item in r.inbox.unread(limit=None):
		continue
	return
	
def main():
	try:
		with open('log.conf') as f:
			logging.config.dictConfig(json.load(f))
		logging.info("Beginning script execution")
		conn = init_database()
		db = conn.cursor()
		r = praw.Reddit('bot1')
		logging.debug("Running bot with user " + str(r.user.me()))	
		crosspost_good_submissions(r, db)
		check_unmoderated_items(r)
		conn.commit()
		conn.close()
	except:
		logging.exception("Unexpected termination")

if __name__ == "__main__":
	main()
