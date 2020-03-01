import data
from apscheduler.schedulers.gevent import GeventScheduler
import time
from datetime import datetime
import praw
from utils import backups


def setup():
    print('setting up Scheduler')
    scheduler = GeventScheduler()
    scheduler.add_job(func=schedule, trigger='cron', **data.update_cron)
    scheduler.start()


def schedule():
    t = int(time.time())
    print(f'{datetime.utcfromtimestamp(t).strftime("%I:%M:%S %p on %b %-d, %Y UTC")}: running scheduled tasks')
    save_time(t)
    if data.TIMES[t] > 0:
        find_deleted(t)
        backups.backup_data()
    print(f' --> scheduled tasks done in {time.time() - t} seconds')

def save_time(t):
    data.TIMES[t] = len(data.RECIEVED)

def find_deleted(t):
    for utt in data.CORPUS.iter_utterances():
        if utt.meta['removed'] > 0 or t - utt.timestamp > data.SEC_PER_DAY:
            continue
        comment = praw.models.Comment(reddit=data.reddit, id=utt.id)
        if comment.body == '[removed]':
            print(f'found removal in comment {utt.id}')
            utt.meta['removed'] = t
