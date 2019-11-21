import convokit
from data import *

def store_data(corpus,t):
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
        POSTS[t][d['leaf'].submission.id][d['leaf'].id] = i
        
    SCORES[t] = ranks
