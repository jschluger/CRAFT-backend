import praw
import convokit
from convokit import Utterance, Conversation, Corpus, User
from pprint import pprint
import data


def add_delta(utt_id):
    utt = data.CORPUS.get_utterance(utt_id)
    d = None
    if (utt.reply_to) in data.CORPUS.utterances:
        parent = data.CORPUS.get_utterance(utt.reply_to)
        if 'craft_score' in utt.meta and 'craft_score' in parent.meta:
            d = utt.meta['craft_score'] - parent.meta['craft_score']

    if d == None:
        utt.meta['delta'] = 0
    else:
        utt.meta['delta'] = d


def wiki_add_delta(utt_id):
    utt = data.WIKI_CORPUS.get_utterance(utt_id)
    d = None
    if (utt.reply_to) in data.WIKI_CORPUS.utterances:
        parent = data.WIKI_CORPUS.get_utterance(utt.reply_to)
        if 'craft_score' in utt.meta and 'craft_score' in parent.meta:
            d = utt.meta['craft_score'] - parent.meta['craft_score']

    if d == None:
        utt.meta['delta'] = 0
    else:
        utt.meta['delta'] = d
