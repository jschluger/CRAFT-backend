import data
import praw
import convokit

def backup_data(t):
    data.CORPUS.dump(data.CORPUS_f, base_path="./")
        

def load_backup():
    data.CORPUS = convokit.Corpus(filename=data.CORPUS_f)
    for utt in data.CORPUS.iter_utterances():
        data.COMMENTS[utt.id] = praw.models.Comment(reddit=data.reddit, id=utt.id)
            
def check_data():
    assert True
