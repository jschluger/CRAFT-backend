import praw
import convokit
import prawcore
from convokit import Utterance, Conversation, Corpus, User
from pprint import pprint
import data
import threading
import time
from utils import live_craft, delta
import sys
from .revision_pipeline import comments


def maintain_corpus(history=False):
    # TODO: FIX WITH JACK
    def background():
        c = 0
        while True:
            try:
                c = 1
                for comment in data.reddit.subreddit('changemyview').stream.comments(skip_existing=not history):
                    add_comment(comment)
                    # show_corpus()
                    data.RECIEVED.append(comment.id)
                    c += 1
                    if c % 500 == 0:
                        print(f'adding leaf comment # {c}; {len(list(data.CORPUS.iter_conversations()))} conversations happening accross {len(data.CORPUS.utterances)} utterances')
                    live_craft.rank_convo(comment.id)
                    delta.add_delta(comment.id)
            except prawcore.exceptions.RequestException as e:
                print(
                    f'got error {e} from subreddit stream; restarting stream')

    if len(data.TIMES) == 0:
        data.TIMES[time.time()] = 0

    thread = threading.Thread(target=background, args=())
    thread.daemon = True
    thread.start()


def ingest_wiki_corpus():
    cg = comments.CommentGenerator(data.WIKI_TOPICS)
    data.WIKI_COMMENTS = cg.curr_corpora
    for topic, commentcorpus in data.WIKI_COMMENTS.items():
        for _, comment in commentcorpus.comment_lookup.items():
            wiki_add_comment(comment)
            data.WIKI_RECEIVED.append(comment.id)
        for _, comment in commentcorpus.comment_lookup.items():
            live_craft.wiki_rank_convo(comment.id)
            delta.wiki_add_delta(comment.id)
    # def background():
    #     for tup in cg.stream():
    #         for topic, comment in tup:
    #             # is already added to WIKI_COMMENTS since WIKI_COMMENTS points to cg
                    # wiki_add_comment(comment)
                    # data.WIKI_RECEIVED.append(comment.id)
                    # live_craft.wiki_rank_convo(comment.id)
                    # delta.wiki_add_delta(comment.id)

def wiki_add_comment(comment):
    meta = {'page': comment.post}
    utt = Utterance(id=comment.id, text=comment.body,
                    reply_to=comment.parent_id, root=comment.root,
                    user=User(id=comment.author),
                    timestamp=comment.created_utc, meta=meta)
    if data.WIKI_CORPUS == None:
        data.WIKI_CORPUS = Corpus(utterances=[utt])
    else:
        data.WIKI_CORPUS = data.WIKI_CORPUS.add_utterances([utt])

def add_comment(comment):
    # first, check if we need to add the parent
    p = comment.parent_id.split('_')
    if p[0] == 't1' and (data.CORPUS == None or p[1] not in data.CORPUS.utterances):
        parent_comment = praw.models.Comment(reddit=data.reddit, id=p[1])
        add_comment(parent_comment)

    # calculate the root
    if p[0] == 't3':
        root = comment.id
        reply = None
        depth = 1
    else:
        assert p[0] == 't1'
        parent = data.CORPUS.get_utterance(p[1])
        if len(parent.meta['children']) == 0:
            add_endings(parent, comment.id, pi=parent.id)
        else:
            add_endings(parent, comment.id)

        parent.meta['children'].append(comment.id)
        root = parent.root
        reply = p[1]
        depth = parent.meta['depth'] + 1

    # add the utterance to the corpus
    post_id = comment.submission.id
    if post_id in data.POSTS:
        data.POSTS[post_id]['convos'] += 1
    else:
        data.POSTS[post_id] = {'title': comment.submission.title,
                               'author': comment.submission.author.name if comment.submission.author is not None else 'n/a',
                               'convos': 1}

    comment_number = data.POSTS[post_id]['convos']

    meta = {'children': [], 'endings': [], 'depth': depth, 'removed': 0,
            'post_id': post_id, 'permalink': comment.permalink, 'comment_number': comment_number}
    utt = Utterance(id=comment.id, text=comment.body,
                    reply_to=reply, root=root,
                    user=User(
                        id=comment.author.name if comment.author is not None else "n/a"),
                    timestamp=comment.created_utc, meta=meta)
    if data.CORPUS == None:
        data.CORPUS = Corpus(utterances=[utt])
    else:
        data.CORPUS = data.CORPUS.add_utterances([utt])


def add_endings(utt, i, pi=None):
    if pi == None:
        utt.meta['endings'].append(i)
    else:
        utt.meta['endings'].append(i)
        if pi in utt.meta['endings']:
            utt.meta['endings'].remove(pi)

    if utt.reply_to != None:
        add_endings(data.CORPUS.get_utterance(utt.reply_to), i, pi=pi)


def show_corpus():
    for i, utt in data.CORPUS.utterances.items():
        print(f'{i} ->  id: {utt.id}, reply_to: {utt.reply_to}, root: {utt.root} ')
