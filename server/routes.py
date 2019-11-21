from flask import Blueprint, request
from data import *
import time

routes = Blueprint('routes', __name__)

def format_score(scoreobj):
    link = f'http://reddit.com{scoreobj["leaf"].permalink}'
    return (scoreobj['score'],link)

@routes.route("/viewtop")
def viewtop():
    k = 20
    t = int(time.time())

    if 'k' in request.values:
        k = request.values['k']
    if 't' in request.values:
        t = request.values['t']

    t_real = 0
    for t_pos in sorted(SCORES.keys()):
        if t_pos > t_real:
            break
        t_real = t_pos
        
    if t_real == 0:
        t_real = t_pos
        
    return {'when': t_real,
            'ranking': list(map(format_score, SCORES[t_real]))[:k] if t_real in scores else None }

@routes.route("/posts")
def posts():
    return POSTS
    
