from apscheduler.schedulers.background import BackgroundScheduler
import time, convokit
from datetime import datetime
from utils import download, craft
from data import *
from pprint import pprint
from collections import defaultdict


def update():
    """
    Download data from reddit, run craft on it, update the data structures with the rankings
    """
    t = int(time.time())
    print(f'==> update at time {t} ({datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")} UTC)...')

    corpus = download.build_corpus(n=1)
    corpus = craft.rank_convos(corpus,run_craft = False)
    store_data(corpus,t)
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

def store_data(corpus,t):
    """
    Given a CRAFT-labeled corpus <corpus> and a time <t>, update data structures <SCORES> and <POSTS>
    to store the CRAFT predictions. 
    """
    ranks = []
    for convo in corpus.iter_conversations():
        d = {}
        score = 0
        com = None
        for utt in convo.iter_utterances():
            com = utt.meta['comment']
            if 'forecast_score_cmv' in utt.meta:
                score = max(score, utt.meta['forecast_score_cmv'])
        d['leaf'] = com
        d['score'] = score
        ranks.append(d)
    ranks = sorted(ranks, key=lambda d: d['score'],reverse=True)

    for i in range(len(ranks)):
        d = ranks[i]
        post = d['leaf'].submission.id
        com = d['leaf'].id
        POSTS[post][t][d['leaf'].id] = i
        
    SCORES[t] = ranks

    
    
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
                

