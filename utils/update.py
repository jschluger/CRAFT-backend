from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from utils import download, craft, live_download
from pprint import pprint
import time, convokit, pickle, os.path, data
import threading

def update():
    """
    Download data from reddit, run craft on it, update the data structures with the rankings
    """
    t = int(time.time())
    print(f'==> update at time {t} ({datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")} UTC)...')

    corpus = download.build_corpus(n=data.p)
    if corpus==None:
        return
    corpus = craft.rank_convos(corpus,run_craft=data.run_craft)
    store_data(corpus,t)
    check_data()
    backup_data(t)

def update_2():
    t = int(time.time())
    print(f'==> update at time {t} ({datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")} UTC)...')
    craft.rank_convos(data.CORPUS, run_craft=data.run_craft)
    store_data(data.CORPUS,t)
    check_data()
    backup_data(t)

    
def setup():
    """
    Set <update> to run at regular intervals
    """
    print('setting up updates')
    scheduler = BackgroundScheduler()
    # scheduler.add_job(func=update, trigger='cron', **data.update_cron)
    scheduler.add_job(func=update_2, trigger='cron', **data.update_cron)
    scheduler.start()
    if data.args.start_from_backup:
        load_backup()
        print('Loaded backup...')
        check_data()
    elif os.path.isfile(data.POSTS_f) or os.path.isfile(data.SCORES_f):
        print( '--------------------------ERROR---------------------------------\n'
               'Did not pass --start_from_backup, but backup files already exist.\n'
               'Pass --start_from_backup to use backed up data, or move backup\n'
              f' files {data.SCORES_f} and {data.POSTS_f} to start from scratch.\n'
               '--------------------------ERROR---------------------------------')
        exit(1)
    live_download.maintain_corpus()
    # print(f'data.ACTIVE initialized to {data.ACTIVE}')

def setup_active():
    for post in data.reddit.subreddit('changemyview').hot(limit=5):
        data.ACTIVE[post.id] = {"post": post,
                                "num_comments": [post.num_comments]}
    return 
    def background():
        for post in data.reddit.subreddit('changemyview').stream.submissions(skip_exsiting=True):
            print(f'adding {post} to active with {post.num_comments} comments')
            data.ACTIVE[post.id] = {"post": post,
                                    "num_comments": [post.num_comments]}
    thread = threading.Thread(target=background, args=())
    thread.daemon = True
    thread.start()
    
def store_data(corpus,t):
    """
    Given a CRAFT-labeled corpus <corpus> and a time <t>, update data structures <data.SCORES> and <data.POSTS>
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
        if post not in data.POSTS:
            data.POSTS[post] = {}
        if t not in data.POSTS[post]:
            data.POSTS[post][t] = {}
        data.POSTS[post][t][d['leaf'].id] = i
        
    data.SCORES[t] = ranks

def backup_data(t):
    with open(data.SCORES_f,'ab') as sf:
        pickle.dump((t,data.SCORES[t]), sf)
    
    with open(data.POSTS_f,'wb') as pf:
        pickle.dump(data.POSTS, pf)

def load_backup():
    with open(data.SCORES_f,'rb') as sf:
        try: 
            while True:
                t,s = pickle.load(sf)
                data.SCORES[t] = s
        except EOFError:
            pass

    with open(data.POSTS_f,'rb') as pf:
        data.POSTS = pickle.load(pf)

        
def check_data():
    """
    Assert the integrity of the data structures. Specificly, assert that all pointers of 
    the form <i = data.POSTS[pid][t][cic]> all point to the score
    <data.SCORES[t][i]> that cooresponds to the right leaf comment <cid>
    """
    print(f'    now tracking {len(data.POSTS.keys())} posts, over {len(data.SCORES.keys())} updates')    
    for pid,times in data.POSTS.items():
        for t,upt in times.items():
            for com,i in sorted(upt.items(), key=lambda t:t[1]):
                scored = data.SCORES[t][i]
                # print(f'at t={t}, post {pid} has leaf {com} with ranked {i}')
                # print(f'\tupdate at {t} has comment {scored["leaf"].id} with score {scored["score"]} ranked {i}')
                assert com==scored["leaf"].id

    # print('SCORES has updates at...')
    # for t,scores in data.SCORES.items():
    #     print(f'\t - <{t}>')
