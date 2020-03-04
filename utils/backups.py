import data
import praw, convokit, pickle

def backup_data():
    data.CORPUS.dump(data.CORPUS_f, base_path="./")

    with open(data.RECIEVED_f,'wb') as f:
        pickle.dump(data.RECIEVED, f)
    with open(data.TIMES_f,'wb') as f:
        pickle.dump(data.TIMES, f)
    with open(data.POSTS_f,'wb') as f:
        pickle.dump(data.POSTS, f)

    
def load_backup():
    data.CORPUS = convokit.Corpus(filename=data.CORPUS_f)
    c = 0
    C = len(list(data.CORPUS.iter_utterances()))
    for utt in data.CORPUS.iter_utterances():
        if c % 50 == 0:
            print(f'{c} / {C}')
        c += 1

    with open(data.RECIEVED_f,'rb') as f:
        data.RECIEVED = pickle.load(f)

    with open(data.TIMES_f,'rb') as f:
        data.TIMES = pickle.load(f)

    with open(data.POSTS_f,'rb') as f:
        data.POSTS = pickle.load(f)
