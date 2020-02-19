import data
from apscheduler.schedulers.background import BackgroundScheduler
import time
from datetime import datetime
import praw
from utils import backups


def setup():
    print('setting up BackgroundScheduler')
    scheduler = BackgroundScheduler()
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
    c = len(data.RECIEVED) - 1
    now = time.time()
    while c >= 0:
        utt = data.CORPUS.get_utterance(data.RECIEVED[c])
        # print(f'c={c}\t utt {utt.id}\t at time {utt.timestamp} \t now={time.time()-now}')
        now = time.time()
        if t - utt.timestamp > data.SEC_PER_DAY:
            break
        if utt.meta['removed'] > 0:
            c -= 1
            continue
        
        check_removed(utt, t)
        c -= 1
        
def check_removed(utt, t):
    comment = praw.models.Comment(reddit=data.reddit, id=utt.id)
    if comment.body == '[removed]':
        print(f'found removal in comment {utt.id}')
        utt.meta['removed'] = t

