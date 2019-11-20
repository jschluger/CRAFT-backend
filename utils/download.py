import praw
import convokit
from convokit import Utterance, Conversation, Corpus, User

reddit = praw.Reddit(client_id='sq6GgQR_4lri7A',
                     client_secret='dWes213OfQWpF7eCVxeImaHSbiw',
                     user_agent='jack')
 
def get_convos(post):
    post.comments.replace_more(limit=0)
    saveto = []
    for comment in post.comments:
        get_convos_itt(comment,saveto,[])
    return sorted(saveto, key=lambda clist: clist[0].score)
 
def get_convos_itt(comment, saveto, acc):
    acc.append(comment)
    if len(comment.replies) == 0:
        saveto.append(acc)
    else:
        for reply in comment.replies:
            get_convos_itt(reply,saveto,acc[:])

def add_convos(clist,corpus=None):
    utts = []
    users = {}
    i = 0 if corpus==None else len(corpus.utterances)
    for comments in clist:
        reply_utt = None
        root_utt = None
        c_utts = []
        for comment in comments:
            if root_utt is None:
                root_utt = i
            if comment.author not in users:
                users[comment.author] = User(name=comment.author)
            m = {'comment': comment}
            utt = Utterance(id=i, text=comment.body, reply_to=reply_utt, root=root_utt, user=users[comment.author], timestamp=comment.created_utc, meta=m)
            c_utts.append(utt)
            reply_utt=i
            i += 1
        utts.extend(c_utts)
    if corpus is None:
        # print(f"making new corpus with {len(utts)} utterances")
        return Corpus(utterances=utts)
    else:
        # print(f"extending corpus by {len(utts)} utterances")
        # print(f'corpus has {len(corpus.utterances)} utterance before extending')
        corpus = corpus.add_utterances(utts)
        # print(f'corpus has {len(corpus.utterances)} utterance after extending')
        
        return corpus

def build_corpus(sub=reddit.subreddit('changemyview'), n=1):
    corpus = None
    for post in sub.hot(limit=n):
        corpus = add_convos(get_convos(post),corpus=corpus)
    return corpus
