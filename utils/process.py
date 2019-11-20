import convokit

def extract_convos(corpus):
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
    return sorted(ranks, key=lambda d: d['score'],reverse=True)
