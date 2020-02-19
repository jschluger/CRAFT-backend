import praw, convokit, prawcore
from convokit import Utterance, Conversation, Corpus, User
from pprint import pprint
import data
import threading, time
from utils import live_craft, delta

def maintain_corpus(history=False):
    def background():
        c = 0
        while True:
            try:
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
                print(f'got error {e} from subreddit stream; restarting stream')

    if len(data.TIMES) == 0:
        data.TIMES[time.time()] = 0
        
    thread = threading.Thread(target=background, args=())
    thread.daemon = True
    thread.start()
    

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
    data.COMMENTS[comment.id] = comment
    _ = comment.submission.title
    meta = {'children': [], 'endings': [], 'depth': depth, 'removed': 0 }
    utt = Utterance(id=comment.id, text=comment.body,
                    reply_to=reply, root=root,
                    user=User(name=comment.author.name if comment.author is not None else "n/a"),
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
    for i,utt in data.CORPUS.utterances.items():
        print(f'{i} ->  id: {utt.id}, reply_to: {utt.reply_to}, root: {utt.root} ')
            
