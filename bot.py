import praw
from pprint import pprint
import sqlite3

conn = sqlite3.connect('db.sqlite')
conn.execute('CREATE TABLE IF NOT EXISTS submissions (name text NOT NULL UNIQUE, title text NOT NULL, hot integer NOT NULL)')
c = conn.cursor()
r = praw.Reddit('bot1')
print(r.user.me())	
c.execute('UPDATE submissions SET hot = 0')
for submission in r.subreddit('nomansskythegame').hot(limit=1000):
	if hasattr(submission,'link_flair_text') and (('Information' in str(submission.link_flair_text)) or ('Discussion' in str(submission.link_flair_text))):
		c.execute('SELECT COUNT(*) FROM submissions WHERE name = ?',(str(submission.name),))
		(number_of_rows,)=c.fetchone()
		if(number_of_rows==0):
			new_submission = submission.crosspost(subreddit="NMS_Discussions",send_replies=False)
			c.execute('INSERT INTO submissions(name,title,hot) VALUES (?,?,1)', (str(submission.name),str(submission.title)))
			new_submission.mod.lock()
			if(not hasattr(submission,'post_hint')):
				new_submission.mod.approve()
			print('NEW: ' + str(submission.title))
		else:
			c.execute('UPDATE submissions SET hot = 1 WHERE name = ?',(str(submission.name),))

c.execute('DELETE FROM submissions WHERE hot = 0')
print('Deleted ' + str(c.rowcount) + ' rows.')
conn.commit()
conn.close()
