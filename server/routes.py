from flask import Blueprint, request
from data import *
import time
import json

routes = Blueprint('routes', __name__)

def format_score(scoreobj):
    link = f'http://reddit.com{scoreobj["leaf"].permalink}'
    return (scoreobj['score'],link)


def vt_json(when=-1, ranking=None):
    return json.dumps(
        {
            'when': when,
            'ranking': ranking
        })

def vt_response(k,t):
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

@routes.route("/posts")
def posts():
    return POSTS
    
