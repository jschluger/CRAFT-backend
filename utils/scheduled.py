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
    save_time()
    find_deleted()
    backups.backup_data()
    print('done with scheduled tasks')

def save_time():
    t = int(time.time())
    data.TIMES[t] = len(data.RECIEVED)
    print(f'--->> setting data.TIMES[{t}] = {data.TIMES[t]}')


def find_deleted():
    for utt in data.CORPUS.iter_utterances():
        comment = praw.models.Comment(reddit=data.reddit, id=utt.id)
        if comment.body != utt.text:
            if comment.body == '[removed]': #  or comment.body == '[deleted]':
                print(f'found removal in comment {utt.id}! \n\t"{utt.text}"\n\t-->\n\t"{comment.body}"')
                utt.meta['removed'] = True
        else:
            utt.meta['removed'] = False
