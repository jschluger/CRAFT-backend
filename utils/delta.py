import praw
import convokit
from convokit import Utterance, Conversation, Corpus, User
from pprint import pprint
import data

def delta(utt_id):
    # utt = data.CORPUS.get_utterance(utt_id)
    # parent = data.CORPUS.get_utterance(utt.reply_to)
    return -1 # utt.meta['forecast_score_cmv'] - parent.meta['forecast_score_cmv']
