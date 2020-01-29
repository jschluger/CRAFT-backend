from flask import Blueprint, request, Response
import time, json, data
from pprint import pprint
from convokit import Utterance, Conversation, Corpus


routes = Blueprint('routes', __name__)

def format_score(scoreobj):
    """ 
    Formats an element of a list stored at data.SCORES[t] to be sent to a client

    :param scoreobj: dict of form
                      {'leaf': praw obj of leaf comment in conversation
                       'score': predicted derailment score of conversation }

    :return: (predicted score, link to leaf comment) tuple
    """
    link = f'http://reddit.com{scoreobj["leaf"].permalink}'
    return (scoreobj['score'], scoreobj['leaf'].id)


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
    resp = Response(js)
    return resp
    
    
def vt_response(k,t, err=False):
    """
    Responds to a viewtop request

    :param when: number of conversations to return
    :param t: requested update time
    
    :return: a correctly formated json response containing the top <k> most likely 
             conversations to derail as predicted during the update taking place
             at the latest time before <t>
    """
    if err==True:
        return format_vt_response()
    
    times = sorted(data.SCORES.keys())
    # print(f'times is {times}')
    if len(times) == 0:
        return format_vt_response()

    # find out_t as latest update time before t    
    out_t = 0
    if t > times[-1]:
        out_t = times[-1]
    elif t < times[0]:
        out_t = times[0]
    else:
        for i,x in enumerate(times):
            if x > t:
                break
        out_t = times[i-1 if i > 0 else 0]

    # if k == -1, return all scores, otherwise return the first k
    if k == -1:
        ranks = list(map(format_score, data.SCORES[out_t]))
    else:
        ranks = list(map(format_score, data.SCORES[out_t][:k]))
        
    return format_vt_response(when= out_t, ranking= ranks)

@routes.route("/viewtop", methods=['POST'])
def viewtop():
    """
    Route to handle viewtop requests
    """
    # Default args
    k = 20
    t = int(time.time())

    # Get args from request
    try:
        if 'k' in request.values:
            k = int(request.values['k'])
        if 't' in request.values:
            t = int(request.values['t'])
    except Exception as e:
        print(f'Recieved error <{e}> while parsing args to viewtop request')
        return vt_response(err=True) # empty response
    
    return vt_response(k,t)


@routes.route("/viewtimes", methods=['POST'])
def viewtimes():
    """
    Route to handle viewtimes
    """
    times = list(data.SCORES.keys())
    js = json.dumps({'times':times})
    resp = Response(js)
    return resp


def format_vc_response(i=-1, parent=None, children=[], convo=None):
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
            'convo': convo
        })
    resp = Response(js)
    return resp

def vc_format(utt):
    return (utt.id, utt.timestamp, utt.meta['forecast_score_cmv'] if 'forecast_score_cmv' in utt.meta else -1)

def vc_response(i=-1, err=False):
    """
    Responds to a viewconvo request

    :param i: id of convo to return
    
    :return: a correctly formated json response for convo <i>
    """
    if err==True or \
       data.CORPUS is None or \
       i not in data.CORPUS.utterances:
        # print(f'returning empty response; \n\terr={err}\n\ti not in data.CORPUS.utterances={i not in data.CORPUS.utterances}\n\ti={i}')
        return format_vc_response()

    utt = data.CORPUS.get_utterance(i)
    convo = []
    print('processing')
    while utt.reply_to is not None:
        convo.append(vc_format(utt))
        utt = data.CORPUS.get_utterance(utt.reply_to)
    print('processed')
    print(f'vc response for id {i} makes convo')
    pprint(convo[::-1])
    ######
    # utt = data.CORPUS.get_utterance(i)
    # c = utt.get_conversation()
    # print('viewing the convokit convo for this utt:')
    # for u in c.iter_utterances():
    #     print(u)

        
    return format_vc_response(i=i, parent=utt.reply_to, children=[], convo=convo[::-1])
    


@routes.route("/viewconvo", methods=['POST'])
def viewconvo():
    """
    Route to handle viewconvo
    """
    # Default args
    
    # Get args from request
    print(f'recieved /viewconvo with args {request.values}')
    i = None
    try:
        if 'id' in request.values:
            i = request.values['id']
    except Exception as e:
        print(f'Recieved error <{e}> while parsing args to viewconvo request')
        return vc_response(err=True) # empty response
    
    return vc_response(i=i)
                        


