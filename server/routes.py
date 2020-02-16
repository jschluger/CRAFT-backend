from flask import Blueprint, request, Response
import time, json, data
from pprint import pprint
from convokit import Utterance, Conversation, Corpus
from utils import delta

routes = Blueprint('routes', __name__)

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

def an_hour_before(t):
    m = t
    cur = t
    for t1 in sorted(data.TIMES.keys(), reverse=True):
        d = abs(t - (60*60) - t1)
        if d < m:
            m = d
            cur = t1
        else:
            break
    return cur
            

def format_vt_response(when=-1, ranking=None):
    """
    Formats a response to a viewtop request
    
    :param when: time of the update
    :param ranking: list of (predicted score, link to leaf comment) tuples 

    :return: json for a viewtop request
    """    
    js = json.dumps(
        {
            'when': when,
            'ranking': ranking
        })
    # print(f'/viewtop sending {js}')
    resp = Response(js)
    return resp
    
@routes.route("/viewtop", methods=['POST'])
def viewtop():
    """
    Route to handle viewtop requests
    """
    entered = time.time()
    # Default args
    
    k = 50
    t = -1
    
    # Get args from request
    try:
        if 'k' in request.values:
            k = int(request.values['k'])
        if 't' in request.values:
            t = int(request.values['t'])
    except Exception as e:
        print(f'Recieved error <{e}> while parsing args to viewtop request')
        return format_vt_response() # empty response

    if t in data.TIMES.keys():
        last = data.TIMES[t]
    else:
        last = len(data.RECIEVED)
        t = -1
    
    t1 = an_hour_before(t if t != -1 else time.time())
    print(f'\tan_hour_before found time {t-t1} seconds before {t}\n\t{time.time()-t1} seconds before now')
    # print(f':: :: :: \t\t\t\t\t {time.time() - entered} \t seconds into /viewtop :: :: ::')
    first = data.TIMES[t1] if t1 in data.TIMES else 0

    ids = data.RECIEVED[first:last]
    # print(f':: :: :: got ids (len is {len(ids)}); \t\t\t {time.time() - entered} \t seconds into /viewtop :: :: ::')
    ids = list(filter(lambda i:
                      is_leaf(data.CORPUS.get_utterance(i),t),
                      ids))
    # print(f':: :: :: filtered ids (len is {len(ids)}); \t\t {time.time() - entered} \t seconds into /viewtop :: :: ::')
    ids.sort(key=lambda i:
             safe_score(data.CORPUS.get_utterance(i)), reverse=True)
    # print(f':: :: :: sorted ids (len is {len(ids)}); \t\t {time.time() - entered} \t seconds into /viewtop :: :: ::')
    ids = ids[:k]
    # print(f':: :: :: sliced ids (len is {len(ids)}); \t\t {time.time() - entered} \t seconds into /viewtop :: :: ::')
    ranking = list(map(lambda i:
                   (
                       safe_score(data.CORPUS.get_utterance(i)),
                       i,
                       safe_delta(data.CORPUS.get_utterance(i)),
                       safe_num_comments(data.CORPUS.get_utterance(i)),
                       data.COMMENTS[i].submission.title
                   ),
                   ids))
    # print(f':: :: :: mapped ids to ranking(len is {len(ranking)});\t {time.time() - entered} \t seconds into /viewtop :: :: ::')
    return format_vt_response(when=t, ranking=ranking)


@routes.route("/viewtimes", methods=['POST'])
def viewtimes():
    """
    get the times
    """
    times = sorted(list(data.TIMES.keys()))[1:]
    js = json.dumps({'times':times})
    resp = Response(js)
    return resp


def format_vc_response(i=-1, parent=None, endings=[], convo=[], post_name="Not a Post", post_author=None):
    """
    Formats a response to a viewtop request
    
    :param i:
    ...

    :return: json for a viewtop request
    """    
    js = json.dumps(
        {
            'id': i,
            'parent': parent,
            'endings': endings,
            'convo': convo,
            'post_name': post_name,
            'post_author': post_author
        })
    resp = Response(js)
    return resp

@routes.route("/viewconvo", methods=['POST'])
def viewconvo():
    """
    Route to handle viewconvo
    """
    # Default args
    
    # Get args from request
    i = None
    try:
        if 'id' in request.values:
            i = request.values['id']
    except Exception as e:
        print(f'Recieved error <{e}> while parsing args to viewconvo request')
        return format_vc_response() # empty response

    if data.CORPUS is None or i not in data.CORPUS.utterances:
        return format_vc_response()

    utt = data.CORPUS.get_utterance(i)
    parent = utt.reply_to
    endings = utt.meta['endings']
    convo = []
    while True:
        comment = data.COMMENTS[utt.id]
        formatted = (utt.id,
                     utt.timestamp,
                     safe_score(utt),
                     utt.text,
                     comment.permalink,
                     safe_author(utt),
                     safe_removed(utt),
                     utt.meta['endings']
        )    
        convo.append(formatted)
        
        if utt.reply_to is None:
            break
        utt = data.CORPUS.get_utterance(utt.reply_to)

    return format_vc_response(i=i, parent=parent, endings=endings, convo=convo[::-1],
                              post_name=comment.submission.title, post_author=safe_post_author(comment))                    


