from apscheduler.schedulers.background import BackgroundScheduler
import time
from utils import download, process, craft
from data import *
from pprint import pprint
from collections import defaultdict

def update():
    """
    Download data from reddit, run craft on it, update the data structures with the rankings
    """
    t = int(time.time())
    print(f'==> update at time {t} ...')

    corpus = download.build_corpus(n=1)
    corpus = craft.rank_convos(corpus,run_craft = False)
    process.store_data(corpus,t)
    print(f'    now tracking {len(POSTS.keys())} posts, over {len(SCORES.keys())} updates')
    check_data()
    
def setup():
    """
    Set <update> to run at regular intervals
    """
    print('setting up updates')
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update, trigger='cron', second='*/5')
    scheduler.start()

    # update()
    # print(f'SCORES = {SCORES}')
    # print(f'POSTS = {POSTS}')

def check_data():
    """
    Assert the integrity of the data structures. Specificly, assert that all pointers of 
    the form <i = POSTS[pid][t][cic]> all point to the score
    <SCORES[t][i]> that cooresponds to the right leaf comment <cid>
    """
    for pid,times in POSTS.items():
        for t,upt in times.items():
            for com,i in sorted(upt.items(), key=lambda t:t[1]):
                scored = SCORES[t][i]
                # print(f'at t={t}, post {pid} has leaf {com} with ranked {i}')
                # print(f'\tupdate at {t} has comment {scored["leaf"].id} with score {scored["score"]} ranked {i}')
                assert com==scored["leaf"].id
                
