from flask import Blueprint, request
from data import *
import time
import json


routes = Blueprint('routes', __name__)

def format_score(scoreobj):
    """ 
    Formats an element of a list stored at SCORES[t] to be sent to a client

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
    times = sorted(SCORES.keys())
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


    return vt_json(when= out_t, ranking= list(map(format_score, SCORES[out_t][:k])) )

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
    except:
        return vt_json() # empty response
    
    return vt_response(k,t)
