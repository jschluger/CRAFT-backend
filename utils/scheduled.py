import data
from apscheduler.schedulers.background import BackgroundScheduler
import time
import praw
from utils import backups


def setup():
    print('setting up BackgroundScheduler')
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=schedule, trigger='cron', **data.update_cron)
    scheduler.start()


def schedule():
    t = int(time.time())
    save_time(t)
    if data.TIMES[t] > 0:
        find_deleted()
        backups.backup_data()
    print(f'done with scheduled tasks in {time.time() - t} seconds')

def save_time(t):
    data.TIMES[t] = len(data.RECIEVED)
    print(f'--->> setting data.TIMES[{t}] = {data.TIMES[t]}')


def find_deleted():
    for utt in data.CORPUS.iter_utterances():
        if utt.meta['removed'] > 0:
            continue
        comment = praw.models.Comment(reddit=data.reddit, id=utt.id)
        if comment.body == '[removed]': #  or comment.body == '[deleted]':
            print(f'found removal in comment {utt.id}! \n\t"{utt.text}"\n\t-->\n\t"{comment.body}"')
            utt.meta['removed'] = time.time()
