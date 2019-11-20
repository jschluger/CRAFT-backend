from apscheduler.schedulers.background import BackgroundScheduler
import time
from utils import download, process, craft
from data import *

def update():
    t = int(time.time())
    print(f'doing update at time {t}')
    corpus = download.build_corpus(n=3)
    corpus = craft.rank_convos(corpus)
    ranks = process.extract_convos(corpus)
    SCORES[t] = ranks
    # print(f'SCORES is now {SCORES}')

def setup():
    print('setting up updates')
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update, trigger='cron', second='0')
    scheduler.start()
    
