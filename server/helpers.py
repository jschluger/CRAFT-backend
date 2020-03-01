import data

def safe_score(utt):
    return utt.meta['craft_score'] if 'craft_score' in utt.meta else 0

def safe_removed(utt):
    return utt.meta['removed'] if 'removed' in utt.meta else 0
    
def safe_num_comments(utt):
    return utt.meta['depth'] if 'depth' in utt.meta else -1

def safe_delta(utt):
    return utt.meta['delta'] if 'delta' in utt.meta else 0

def is_leaf(utt,t):
    if t == -1:
        return len(utt.meta['children']) == 0
    else:
        for cid in utt.meta['children']:
            child = data.CORPUS.get_utterance(cid)
            if child.timestamp < t:
                return False
        return True

def safe_author(utt):
    return utt.user.name

def safe_post_author(com):
    if com.submission.author is not None:
        return com.submission.author.name
    else:
        return 'n/a'
    
def safe_crawl_children(utt, t):
    """
    returns ( num_new_comments, has_derailed_since, still_active )
    """
    n = len(utt.meta['children'])
    derailed = utt.meta['removed'] > 0 or utt.text == '[removed]'
    active   = t - utt.timestamp < data.SEC_PER_DAY
    for cid in utt.meta['children']:
        cN, cA, cD = safe_crawl_children(data.CORPUS.get_utterance(cid), t)
        n += cN
        active = active or cA
        derailed = derailed or cD
    return n, derailed, active

def safe_has_derailed_since(utt):
    return False


def safe_still_active(utt):
    return False


def an_hour_before(t):
    m = t
    cur = t
    for t1 in sorted(data.TIMES.keys(), reverse=True):
        d = abs(t - ( data.SEC_PER_HOUR ) - t1)
        if d < m:
            m = d
            cur = t1
        else:
            break
    return cur
