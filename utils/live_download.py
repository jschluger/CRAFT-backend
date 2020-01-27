import praw
import convokit
from convokit import Utterance, Conversation, Corpus, User
from pprint import pprint
import data
import threading

def maintain_corpus():
    def background():
        c = 0
        for comment in data.reddit.subreddit('changemyview').stream.comments():
            add_comment(comment)
            # show_corpus()
            c += 1
            print(f'adding leaf comment # {c}; {len(list(data.CORPUS.iter_conversations()))} conversations happening accross {len(data.CORPUS.utterances)} utterances')
                                    
    thread = threading.Thread(target=background, args=())
    thread.daemon = True
    thread.start()

def add_comment(comment):
    # print(f'want to add {comment} to corpus')
    # first, check if we need to add the parent
    p = comment.parent_id.split('_')
    # print(f'parent id is {p}')
    if p[0] == 't1' and (data.CORPUS == None or p[1] not in data.CORPUS.utterances):
        parent_comment = praw.models.Comment(reddit=data.reddit, id=p[1])
        add_comment(parent_comment)

    # calculate the root
    # print(f'comment {comment.id} has p[0]=={p[0]}')
    if p[0] == 't3':
        root = comment.id
        reply = None
    else:
        assert p[0] == 't1' 
        root = data.CORPUS.get_utterance(p[1]).root
        reply = p[1]

    # add the utterance to the corpus
    m = {'comment': comment}
    utt = Utterance(id=comment.id, text=comment.body,
                    reply_to=reply, root=root,
                    user=User(name=comment.author),
                    timestamp=comment.created_utc, meta=m)
    # print(f'adding utterance {utt} to corpus')
    if data.CORPUS == None:
        data.CORPUS = Corpus(utterances=[utt])
    else:
        data.CORPUS = data.CORPUS.add_utterances([utt])
    # print(f'corpus is now')
    # show_corpus()

def show_corpus():
    for i,utt in data.CORPUS.utterances.items():
        print(f'{i} ->  id: {utt.id}, reply_to: {utt.reply_to}, root: {utt.root} ')
            
