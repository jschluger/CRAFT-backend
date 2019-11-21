from apscheduler.schedulers.background import BackgroundScheduler
import time
from utils import download, process, craft
from data import *

from collections import defaultdict

def update():
    t = int(time.time())
    print(f'doing update at time {t}')
    POSTS[t] = defaultdict(dict)
    corpus = download.build_corpus(n=1)
    corpus = craft.rank_convos(corpus)
    process.store_data(corpus,t)
    
def setup():
    print('setting up updates')
    # scheduler = BackgroundScheduler()
    # scheduler.add_job(func=update, trigger='cron', second='0')
    # scheduler.start()
    update()
    print(f'SCORES = {SCORES}')
    print(f'POSTS = {POSTS}')
