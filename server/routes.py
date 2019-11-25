from flask import Blueprint, request
import time, json, data


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
    return (scoreobj['score'],link)


def vt_json(when=-1, ranking=None):
    """
    Formats a json response to a viewtop request
    
    :param when: time of the update
    :param ranking: list of (predicted score, link to leaf comment) tuples 

    :return: json for a viewtop request
    """    
    return json.dumps(
        {
            'when': when,
            'ranking': ranking
        })

def vt_response(k,t):
    """
    Responds to a viewtop request

    :param when: number of conversations to return
    :param t: requested update time
    
    :return: a correctly formated json response containing the top <k> most likely 
             conversations to derail as predicted during the update taking place
             at the latest time before <t>
    """
    times = sorted(data.SCORES.keys())
    # print(f'times is {times}')
    if len(times) == 0:
        return vt_json()

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
        
    return vt_json(when= out_t, ranking= ranks)

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
        return vt_json() # empty response
    
    return vt_response(k,t)


@routes.route("/viewtimes", methods=['GET','POST'])
def viewtimes():
    """
    Route to handle viewtimes
    """
    times = list(data.SCORES.keys())
    return json.dumps({'times':times})


