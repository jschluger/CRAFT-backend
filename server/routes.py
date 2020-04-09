from flask import Blueprint, request, Response
import time, json, data
from pprint import pprint
from convokit import Utterance, Conversation, Corpus
from utils import delta
from server.helpers import *

routes = Blueprint('routes', __name__)            

def format_vt_response(when=-1, ranking=None, duration=0, distrib=(0,1)):
    """
    Formats a response to a viewtop request
    
    :param when: time of the update
    :param ranking: list of (...) tuples

    :return: json for a viewtop request
    """    
    js = json.dumps(
        {
            'when': when,
            'ranking': ranking,
            'duration': duration,
            'distrib': distrib
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

    if t == -1:
        now = time.time()
        t1 = an_hour_before(now)
        duration = now-t1
    else:
        t1 = an_hour_before(t)
        duration = t-t1
    
    first = data.TIMES[t1] if t1 in data.TIMES else 0

    ids = data.RECIEVED[first:last]
    ids = list(filter(lambda i:
                      is_leaf(data.CORPUS.get_utterance(i),t),
                      ids))
    ids.sort(key=lambda i:
             safe_score(data.CORPUS.get_utterance(i)), reverse=True)

    n_derail = 0
    for idx, i in enumerate(ids):
        if safe_score(data.CORPUS.get_utterance(i)) < data.THRESHOLD:
            n_derail = idx
            break
    distrib = (n_derail, len(ids))

    ids = ids[:k]
    ranking = []
    for i in ids:
        utt = data.CORPUS.get_utterance(i)
        num_new_comments, has_derailed_since, still_active = safe_crawl_children(utt, t)
        item = {'score': safe_score(utt),
                 'id': i,
                 'delta': safe_delta(utt),
                 'n_comments': safe_num_comments(utt),
                 'convo_name': get_convo_name(utt),
                 'n_new_comments': num_new_comments,
                 'has_derailed': has_derailed_since,
                 'still_active': still_active
        }
        ranking.append(item)
        
    return format_vt_response(when=t, ranking=ranking, duration=duration, distrib=distrib)

@routes.route("/wiki/viewtop", methods=['POST'])
def wiki_viewtop():
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



    ids = data.WIKI_CORPUS.get_utterance_ids()
    ids.sort(key=lambda i: safe_score(data.WIKI_CORPUS.get_utterance(i)), reverse=True)

    n_derail = 0
    for idx, i in enumerate(ids):
        if safe_score(data.WIKI_CORPUS.get_utterance(i)) < data.THRESHOLD:
            n_derail = idx
            break
    distrib = (n_derail, len(ids))

    ranking = []
    for i in ids:
        utt = data.WIKI_CORPUS.get_utterance(i)
        root = data.WIKI_CORPUS.get_utterance(utt.root)
        item = {'score': safe_score(utt),
                 'id': i,
                 'delta': utt.meta.get("delta", 0),
                 'n_comments': -1,
                 'convo_name': utt.meta['page'] + ": " + root.text.replace("#", ""),
                 'n_new_comments': 0,
                 'has_derailed': 0,
                 'still_active': 0
        }
        ranking.append(item)
        
    return format_vt_response(when=0, ranking=ranking, duration=0, distrib=distrib)


@routes.route("/viewtimes", methods=['POST'])
def viewtimes():
    """
    get the times
    """
    times = sorted(list(data.TIMES.keys()))[1:]
    js = json.dumps({'times':times})
    resp = Response(js)
    return resp


def format_vc_response(i=-1, parent=None, endings=[], convo=[], convo_name="n/a", post_author=None):
    """
    Formats a response to a viewconvo request
    
    :param i:
    ...

    :return: json for a viewconvo request
    """    
    js = json.dumps(
        {
            'id': i,
            'parent': parent,
            'endings': endings,
            'convo': convo,
            'convo_name': convo_name,
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
    endings = get_named_endings(utt)
    convo_name=get_convo_name(utt)
    post_author=safe_post_author(utt)
    
    convo = []
    while True:
        formatted = {'id': utt.id,
                     'timestamp': utt.timestamp,
                     'score': safe_score(utt),
                     'text': utt.text,
                     'permalink': utt.meta['permalink'],
                     'author': safe_author(utt),
                     'removed': safe_removed(utt),
        }    
        convo.append(formatted)
        
        if utt.reply_to is None:
            break
        utt = data.CORPUS.get_utterance(utt.reply_to)

    return format_vc_response(i=i, parent=parent, endings=endings, convo=convo[::-1],
                              convo_name=convo_name, post_author=post_author)         

@routes.route("/wiki/viewconvo", methods=['POST'])
def wiki_viewconvo():
    """
    Route to handle wiki viewconvo
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

    if data.WIKI_CORPUS is None or i not in data.WIKI_CORPUS.utterances:
        return format_vc_response()

    utt = data.WIKI_CORPUS.get_utterance(i)
    root = data.WIKI_CORPUS.get_utterance(utt.root)
    parent = utt.reply_to
    convo_name = utt.meta['page'] + ": " + root.text.strip("=")
    # post_author= utt.user # does not really apply
    
    convo = []
    while True:
        formatted = {'id': utt.id,
                     'timestamp': utt.timestamp,
                     'score': utt.meta.get("craft_score", 0),
                     'text': utt.text,
                     'permalink': "",
                     'author': utt.user.name,
                     'removed': 0,
        }    
        convo.append(formatted)
        
        if utt.reply_to is None:
            break
        utt = data.WIKI_CORPUS.get_utterance(utt.reply_to)

    return format_vc_response(i=i, parent=parent, endings=[], convo=convo[::-1],
                              convo_name=convo_name, post_author="")              


