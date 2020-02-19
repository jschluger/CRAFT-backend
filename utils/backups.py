import data
import praw, convokit, pickle

def backup_data():
    data.CORPUS.dump(data.CORPUS_f, base_path="./")

    with open(data.RECIEVED_f,'wb') as f:
        pickle.dump(data.RECIEVED, f)
    with open(data.TIMES_f,'wb') as f:
        pickle.dump(data.TIMES, f)

    
def load_backup(download_reddit=True):
    data.CORPUS = convokit.Corpus(filename=data.CORPUS_f)
    for utt in data.CORPUS.iter_utterances():
        data.COMMENTS[utt.id] = praw.models.Comment(reddit=data.reddit, id=utt.id)
        if download_reddit:
            _ = data.COMMENTS[utt.id].body
            _ = data.COMMENTS[utt.id].submission.title

    with open(data.RECIEVED_f,'rb') as f:
        data.RECIEVED = pickle.load(f)

    with open(data.TIMES_f,'rb') as f:
        data.TIMES = pickle.load(f)
