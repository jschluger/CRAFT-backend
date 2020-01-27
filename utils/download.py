import praw
import convokit
from convokit import Utterance, Conversation, Corpus, User
from pprint import pprint
import data

# get a praw reddit object


def get_convos(post):
    """
    Get a list of conversations taking place on post <post>, where each conversation
    is represented as a list of comment objects
    """
    
    post.comments.replace_more(limit=0)
    saveto = []
    for comment in post.comments:
        get_convos_itt(comment,saveto,[])
    return sorted(saveto, key=lambda clist: clist[0].score)
 
def get_convos_itt(comment, saveto, acc):
    """
    Iterative helper function for get_convos
    """
    acc.append(comment)
    if len(comment.replies) == 0:
        saveto.append(acc)
    else:
        for reply in comment.replies:
            get_convos_itt(reply,saveto,acc[:])

def add_convos(clist,corpus=None):
    """
    Add the conversations <clist> (given in the form returned by <get_convos>) to corpus <corpus>
    """
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
        return Corpus(utterances=utts)
    else:
        corpus = corpus.add_utterances(utts)
        return corpus

def build_corpus(sub=data.reddit.subreddit('changemyview'), n=1):
    """
    Build a corpus from subreddit <sub> from the conversations taking place in the comments
    of the current top <n> hotest posts on the subreddit. 
    """
    if len(data.ACTIVE)==0:
        return None

    corpus = None
    for post_id, D in data.ACTIVE.items():
        corpus = add_convos(get_convos(D['post']),corpus=corpus)
        D['num_comments'].append(D['post'].num_comments)
        
    maintain_active()
    return corpus

def maintain_active():
    print(f'maintaing active:')
    pprint(data.ACTIVE)
    for post_id, D in data.ACTIVE.items():
        if len(D['num_comments']) >= 3 and \
           D['num_comments'][-1] == D['num_comments'][-2] and \
           D['num_comments'][-1] == D['num_comments'][-2]:
            del data.ACTIVE[post_id]
            print(f'{post_id} has not changed for the past 3 updates, removing')
