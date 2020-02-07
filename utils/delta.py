import praw
import convokit
from convokit import Utterance, Conversation, Corpus, User
from pprint import pprint
import data

def delta(utt_id):
    utt = data.CORPUS.get_utterance(utt_id)
    if (utt.reply_to) in data.CORPUS.utterances:
        parent = data.CORPUS.get_utterance(utt.reply_to)
        if 'craft_score' in utt.meta and 'craft_score' in parent.meta:
            return utt.meta['craft_score'] - parent.meta['craft_score']
    
    return 0
    
