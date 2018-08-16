import praw
from pprint import pprint
import sqlite3

def is_good_submission(submission):
	if(submission.score < 5 or submission.num_comments < 5):
		return False

	if (hasattr(submission,'link_flair_text') 
		and (('Information' in str(submission.link_flair_text)) 
			or ('Discussion' in str(submission.link_flair_text)))):
		return True

	if(submission.is_self):
		return True

	return False

conn = sqlite3.connect('db.sqlite')
conn.execute('CREATE TABLE IF NOT EXISTS submissions (name text NOT NULL UNIQUE, title text NOT NULL, hot integer NOT NULL)')
db = conn.cursor()
r = praw.Reddit('bot1')
print(r.user.me())	

db.execute('UPDATE submissions SET hot = hot + 1')
for submission in r.subreddit('nomansskythegame').hot(limit=1000):
	if is_good_submission(submission):
		db.execute('SELECT COUNT(*) FROM submissions WHERE name = ?',(str(submission.name),))
		(number_of_rows,) = db.fetchone()
		if(number_of_rows != 0):
			db.execute('UPDATE submissions SET hot = 0 WHERE name = ?',(str(submission.name),))
			continue
		new_submission = submission.crosspost(subreddit="NMS_Discussions", send_replies=False)
		db.execute('INSERT INTO submissions(name,title,hot) VALUES (?,?,1)', (str(submission.name),str(submission.title)))
		new_submission.mod.lock()
		if(not hasattr(submission,'post_hint') and submission.num_crossposts == 0):
			new_submission.mod.approve()
		print('NEW: ' + str(submission.title))

db.execute('DELETE FROM submissions WHERE hot > 3')
print('Deleted ' + str(db.rowcount) + ' rows.')
conn.commit()
conn.close()
