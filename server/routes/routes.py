from flask import Blueprint
from data import *

routes = Blueprint('routes', __name__)

def format_score(score):
    link = f'http://reddit.com{score["leaf"].permalink}'
    return (score['score'],link)

@routes.route("/")
def base():
    try:
        t = max(SCORES.keys())
        return {'ranks': list(map(format_score, SCORES[t]))}
    except:
        return {}
