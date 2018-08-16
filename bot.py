import praw
from pprint import pprint
import sqlite3

def is_good_submission(submission):
	if(submission.num_comments < 5):
		return False

	if (hasattr(submission,'link_flair_text') 
		and (('Information' in str(submission.link_flair_text).title()) 
			or ('Discussion' in str(submission.link_flair_text).title()))):
		return True

	if(submission.is_self):
		return True

	return False

def get_flair_text(submission):
	if hasattr(submission,'link_flair_text'):
		if('Discussion' in str(submission.link_flair_text).title()):
			return 'Discussion'
		if('Suggestion' in str(submission.link_flair_text).title()):
			return 'Suggestion'
	return 'Information'

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
		has_crossposts = submission.num_crossposts != 0
		new_submission = submission.crosspost(subreddit="NMS_Discussions", send_replies=False)
		db.execute('INSERT INTO submissions(name,title,hot) VALUES (?,?,1)', (str(submission.name),str(submission.title)))
		new_submission.mod.lock()
		new_submission.mod.flair(text=get_flair_text(submission))
		if(not hasattr(submission,'post_hint') and not has_crossposts):
			new_submission.mod.approve()
		print('NEW: ' + str(submission.title))

db.execute('DELETE FROM submissions WHERE hot > 3')
print('Deleted ' + str(db.rowcount) + ' rows.')
conn.commit()
conn.close()
