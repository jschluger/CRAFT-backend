from flask import Blueprint, request, Response
import time, json, data
from pprint import pprint
from convokit import Utterance, Conversation, Corpus
from utils import delta

routes = Blueprint('routes', __name__)

def safe_score(i):
    utt = data.CORPUS.get_utterance(i)
    return utt.meta['craft_score'] if 'craft_score' in utt.meta else -2

def is_leaf(i):
    utt = data.CORPUS.get_utterance(i)
    return len(utt.meta['children']) == 0

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

    # print(f'processing /viewtop(k={k},t={t}')
    
    if t in data.TIMES.keys():
        last = data.TIMES[t]
    else:
        last = len(data.RECIEVED)
        t = -1

    t1 = t - (60 * 60) # one hour earlier
    if t1 in data.TIMES.keys():
        first = data.TIMES[t1]
    else:
        first = 0
        
    # print(f'last is {last}')
    ids = data.RECIEVED[first:last]
    ids = list(filter(lambda i:
                      is_leaf(i),
                      ids))
    ids.sort(key=lambda i:
             safe_score(i), reverse=True)
    ids = ids[:k]
    ranking = list(map(lambda i:
                   (
                       safe_score(i),
                       i,
                       delta.delta(i)
                   ),
                   ids))
    # print(f'ranking is {ranking}')
    return format_vt_response(when=t, ranking=ranking)


@routes.route("/viewtimes", methods=['POST'])
def viewtimes():
    """
    get the times
    """
    times = sorted(list(data.TIMES.keys()))
    js = json.dumps({'times':times})
    resp = Response(js)
    return resp


def format_vc_response(i=-1, parent=None, children=[], convo=[], post_name="Not a Post"):
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
            'children': children,
            'convo': convo,
            'post_name': post_name
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
    children = utt.meta['children']
    convo = []
    # print('processing')
    while True:
        comment = data.COMMENTS[utt.id]
        formatted = (utt.id, utt.timestamp,
            utt.meta['craft_score'] if 'craft_score' in utt.meta else -1,\
            utt.text,
            comment.permalink,
            comment.author.name)    
        convo.append(formatted)

        if utt.reply_to is None:
            break
        utt = data.CORPUS.get_utterance(utt.reply_to)

    return format_vc_response(i=i, parent=parent, children=children, convo=convo[::-1], post_name=comment.submission.title)                    


