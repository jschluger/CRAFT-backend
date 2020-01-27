import torch
from torch.jit import script, trace
import torch.nn as nn
from torch import optim
import torch.nn.functional as F
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import nltk
import requests
import os
import sys
import random
import unicodedata
import itertools
from pprint import pprint
from urllib.request import urlretrieve
from convokit import download, Corpus, Utterance, Conversation, User

# define globals and constants

MAX_LENGTH = 80  # Maximum sentence length (number of tokens) to consider

# configure model
hidden_size = 500
encoder_n_layers = 2
context_encoder_n_layers = 2
decoder_n_layers = 2
dropout = 0.1
batch_size = 64
# Configure training/optimization
clip = 50.0
teacher_forcing_ratio = 1.0
learning_rate = 0.0001
labeled_learning_rate = 1e-5
decoder_learning_ratio = 5.0
print_every = 10

# Default word tokens
PAD_token = 0  # Used for padding short sentences
SOS_token = 1  # Start-of-sentence token
EOS_token = 2  # End-of-sentence token
UNK_token = 3  # Unknown word token

# model download paths
WORD2INDEX_URL = {'cmv': "http://zissou.infosci.cornell.edu/convokit/models/craft_cmv/word2index.json", 
                  'wikiconv' : "http://zissou.infosci.cornell.edu/convokit/models/craft_wikiconv/word2index.json" }
INDEX2WORD_URL = {'cmv':  "http://zissou.infosci.cornell.edu/convokit/models/craft_cmv/index2word.json", 
                  'wikiconv': "http://zissou.infosci.cornell.edu/convokit/models/craft_wikiconv/index2word.json" }
                 
MODEL_URL = {'cmv': "http://zissou.infosci.cornell.edu/convokit/models/craft_cmv/craft_full.tar", 
             'wikiconv' : "http://zissou.infosci.cornell.edu/convokit/models/craft_wikiconv/craft_full.tar" }
             

# confidence score threshold for declaring a positive prediction.
# this value was previously learned on the validation set.
FORECAST_THRESH = 0.548580

class Voc:
    """A class for representing the vocabulary used by a CRAFT model"""

    def __init__(self, name, word2index=None, index2word=None):
        self.name = name
        self.trimmed = False if not word2index else True # if a precomputed vocab is specified assume the user wants to use it as-is
        self.word2index = word2index if word2index else {"UNK": UNK_token}
        self.word2count = {}
        self.index2word = index2word if index2word else {PAD_token: "PAD", SOS_token: "SOS", EOS_token: "EOS", UNK_token: "UNK"}
        self.num_words = 4 if not index2word else len(index2word)  # Count SOS, EOS, PAD, UNK

    def addSentence(self, sentence):
        for word in sentence.split(' '):
            self.addWord(word)

    def addWord(self, word):
        if word not in self.word2index:
            self.word2index[word] = self.num_words
            self.word2count[word] = 1
            self.index2word[self.num_words] = word
            self.num_words += 1
        else:
            self.word2count[word] += 1

    # Remove words below a certain count threshold
    def trim(self, min_count):
        if self.trimmed:
            return
        self.trimmed = True

        keep_words = []

        for k, v in self.word2count.items():
            if v >= min_count:
                keep_words.append(k)

        print('keep_words {} / {} = {:.4f}'.format(
            len(keep_words), len(self.word2index), len(keep_words) / len(self.word2index)
        ))

        # Reinitialize dictionaries
        self.word2index = {"UNK": UNK_token}
        self.word2count = {}
        self.index2word = {PAD_token: "PAD", SOS_token: "SOS", EOS_token: "EOS", UNK_token: "UNK"}
        self.num_words = 4 # Count default tokens

        for word in keep_words:
            self.addWord(word)

# Create a Voc object from precomputed data structures
def loadPrecomputedVoc(corpus_name, word2index_url, index2word_url):
    # load the word-to-index lookup map
    r = requests.get(word2index_url)
    word2index = r.json()
    # load the index-to-word lookup map
    r = requests.get(index2word_url)
    index2word = r.json()
    return Voc(corpus_name, word2index, index2word)

# Helper functions for preprocessing and tokenizing text

# Turn a Unicode string to plain ASCII, thanks to
# https://stackoverflow.com/a/518232/2809427
def unicodeToAscii(s):
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

# Tokenize the string using NLTK
def tokenize(text):
    tokenizer = nltk.tokenize.RegexpTokenizer(pattern=r'\w+|[^\w\s]')
    # simplify the problem space by considering only ASCII data
    cleaned_text = unicodeToAscii(text.lower())

    # if the resulting string is empty, nothing else to do
    if not cleaned_text.strip():
        return []
    
    return tokenizer.tokenize(cleaned_text)

# Given a ConvoKit conversation, preprocess each utterance's text by tokenizing and truncating.
# Returns the processed dialog entry where text has been replaced with a list of
# tokens, each no longer than MAX_LENGTH - 1 (to leave space for the EOS token)
def processDialog(voc, dialog):
    processed = []
    for utterance in dialog.iter_utterances():
        # skip the section header, which does not contain conversational content -> not relevant for reddit
        # if utterance.meta['is_section_header']:
        #    continue
        tokens = tokenize(utterance.text)
        # replace out-of-vocabulary tokens
        for i in range(len(tokens)):
            if tokens[i] not in voc.word2index:
                tokens[i] = "UNK"
        # processed.append({"tokens": tokens, "is_attack": int(dialog.meta['has_removed_comment']), "id": utterance.id})
        processed.append({"tokens": tokens, "is_attack": 0, "id": utterance.id})
    return processed

# Load context-reply pairs from the Corpus, optionally filtering to only conversations
# from the specified split (train, val, or test).
# Each conversation, which has N comments (not including the section header) will
# get converted into N-1 comment-reply pairs, one pair for each reply 
# (the first comment does not reply to anything).
# Each comment-reply pair is a tuple consisting of the conversational context
# (that is, all comments prior to the reply), the reply itself, the label (that
# is, whether the reply contained a derailment event), and the comment ID of the
# reply (for later use in re-joining with the ConvoKit corpus).
# The function returns a list of such pairs.
def loadPairs(voc, corpus, split=None):
    pairs = []
    for convo in corpus.iter_conversations():
        # consider only conversations in the specified split of the data
        if split is None or convo.meta['split'] == split:
            dialog = processDialog(voc, convo)
            # context = [u["tokens"][:(MAX_LENGTH-1)] for u in dialog]
            # label = dialog[-1]["is_attack"]
            # comment_id = dialog[-1]["id"]
            # pairs.append((context,"",label, comment_id)) 
            for idx in range(1, len(dialog)):
                reply = dialog[idx]["tokens"][:(MAX_LENGTH-1)]
                label = dialog[idx]["is_attack"]
                comment_id = dialog[idx]["id"]
                # gather as context all utterances preceding the reply
                context = [u["tokens"][:(MAX_LENGTH-1)] for u in dialog[:idx]]
                pairs.append((context, reply, label, comment_id))
    return pairs

# Helper functions for turning dialog and text sequences into tensors, and manipulating those tensors

def indexesFromSentence(voc, sentence):
    return [voc.word2index[word] for word in sentence] + [EOS_token]

def zeroPadding(l, fillvalue=PAD_token):
    return list(itertools.zip_longest(*l, fillvalue=fillvalue))

def binaryMatrix(l, value=PAD_token):
    m = []
    for i, seq in enumerate(l):
        m.append([])
        for token in seq:
            if token == PAD_token:
                m[i].append(0)
            else:
                m[i].append(1)
    return m

# Takes a batch of dialogs (lists of lists of tokens) and converts it into a
# batch of utterances (lists of tokens) sorted by length, while keeping track of
# the information needed to reconstruct the original batch of dialogs
def dialogBatch2UtteranceBatch(dialog_batch):
    utt_tuples = [] # will store tuples of (utterance, original position in batch, original position in dialog)
    for batch_idx in range(len(dialog_batch)):
        dialog = dialog_batch[batch_idx]
        for dialog_idx in range(len(dialog)):
            utterance = dialog[dialog_idx]
            utt_tuples.append((utterance, batch_idx, dialog_idx))
    # sort the utterances in descending order of length, to remain consistent with pytorch padding requirements
    utt_tuples.sort(key=lambda x: len(x[0]), reverse=True)
    # return the utterances, original batch indices, and original dialog indices as separate lists
    utt_batch = [u[0] for u in utt_tuples]
    batch_indices = [u[1] for u in utt_tuples]
    dialog_indices = [u[2] for u in utt_tuples]
    return utt_batch, batch_indices, dialog_indices

# Returns padded input sequence tensor and lengths
def inputVar(l, voc):
    indexes_batch = [indexesFromSentence(voc, sentence) for sentence in l]
    lengths = torch.tensor([len(indexes) for indexes in indexes_batch])
    padList = zeroPadding(indexes_batch)
    padVar = torch.LongTensor(padList)
    return padVar, lengths

# Returns padded target sequence tensor, padding mask, and max target length
def outputVar(l, voc):
    indexes_batch = [indexesFromSentence(voc, sentence) for sentence in l]
    max_target_len = max([len(indexes) for indexes in indexes_batch])
    padList = zeroPadding(indexes_batch)
    mask = binaryMatrix(padList)
    mask = torch.ByteTensor(mask)
    padVar = torch.LongTensor(padList)
    return padVar, mask, max_target_len

# Returns all items for a given batch of pairs
def batch2TrainData(voc, pair_batch, already_sorted=False):
    if not already_sorted:
        pair_batch.sort(key=lambda x: len(x[0]), reverse=True)
    input_batch, output_batch, label_batch, id_batch = [], [], [], []
    for pair in pair_batch:
        input_batch.append(pair[0])
        output_batch.append(pair[1])
        label_batch.append(pair[2])
        id_batch.append(pair[3])
    dialog_lengths = torch.tensor([len(x) for x in input_batch])
    input_utterances, batch_indices, dialog_indices = dialogBatch2UtteranceBatch(input_batch)
    inp, utt_lengths = inputVar(input_utterances, voc)
    output, mask, max_target_len = outputVar(output_batch, voc)
    label_batch = torch.FloatTensor(label_batch) if label_batch[0] is not None else None
    return inp, dialog_lengths, utt_lengths, batch_indices, dialog_indices, label_batch, id_batch, output, mask, max_target_len

def batchIterator(voc, source_data, batch_size, shuffle=True):
    cur_idx = 0
    if shuffle:
        random.shuffle(source_data)
    while True:
        if cur_idx >= len(source_data):
            cur_idx = 0
            if shuffle:
                random.shuffle(source_data)
        batch = source_data[cur_idx:(cur_idx+batch_size)]
        # the true batch size may be smaller than the given batch size if there is not enough data left
        true_batch_size = len(batch)
        # ensure that the dialogs in this batch are sorted by length, as expected by the padding module
        batch.sort(key=lambda x: len(x[0]), reverse=True)
        # for analysis purposes, get the source dialogs and labels associated with this batch
        batch_dialogs = [x[0] for x in batch]
        batch_labels = [x[2] for x in batch]
        # convert batch to tensors
        batch_tensors = batch2TrainData(voc, batch, already_sorted=True)
        yield (batch_tensors, batch_dialogs, batch_labels, true_batch_size) 
        cur_idx += batch_size

        
class EncoderRNN(nn.Module):
    """This module represents the utterance encoder component of CRAFT, responsible for creating vector representations of utterances"""
    def __init__(self, hidden_size, embedding, n_layers=1, dropout=0):
        super(EncoderRNN, self).__init__()
        self.n_layers = n_layers
        self.hidden_size = hidden_size
        self.embedding = embedding

        # Initialize GRU; the input_size and hidden_size params are both set to 'hidden_size'
        #   because our input size is a word embedding with number of features == hidden_size
        self.gru = nn.GRU(hidden_size, hidden_size, n_layers,
                          dropout=(0 if n_layers == 1 else dropout), bidirectional=True)
        
    def forward(self, input_seq, input_lengths, hidden=None):
        # Convert word indexes to embeddings
        embedded = self.embedding(input_seq)
        # Pack padded batch of sequences for RNN module
        packed = torch.nn.utils.rnn.pack_padded_sequence(embedded, input_lengths)
        # Forward pass through GRU
        outputs, hidden = self.gru(packed, hidden)
        # Unpack padding
        outputs, _ = torch.nn.utils.rnn.pad_packed_sequence(outputs)
        # Sum bidirectional GRU outputs
        outputs = outputs[:, :, :self.hidden_size] + outputs[:, : ,self.hidden_size:]
        # Return output and final hidden state
        return outputs, hidden

class ContextEncoderRNN(nn.Module):
    """This module represents the context encoder component of CRAFT, responsible for creating an order-sensitive vector representation of conversation context"""
    def __init__(self, hidden_size, n_layers=1, dropout=0):
        super(ContextEncoderRNN, self).__init__()
        self.n_layers = n_layers
        self.hidden_size = hidden_size
        
        # only unidirectional GRU for context encoding
        self.gru = nn.GRU(hidden_size, hidden_size, n_layers,
                          dropout=(0 if n_layers == 1 else dropout), bidirectional=False)
        
    def forward(self, input_seq, input_lengths, hidden=None):
        # Pack padded batch of sequences for RNN module
        packed = torch.nn.utils.rnn.pack_padded_sequence(input_seq, input_lengths)
        # Forward pass through GRU
        outputs, hidden = self.gru(packed, hidden)
        # Unpack padding
        outputs, _ = torch.nn.utils.rnn.pad_packed_sequence(outputs)
        # return output and final hidden state
        return outputs, hidden
        
class SingleTargetClf(nn.Module):
    """This module represents the CRAFT classifier head, which takes the context encoding and uses it to make a forecast"""
    def __init__(self, hidden_size, dropout=0.1):
        super(SingleTargetClf, self).__init__()
        
        self.hidden_size = hidden_size
        
        # initialize classifier
        self.layer1 = nn.Linear(hidden_size, hidden_size)
        self.layer1_act = nn.LeakyReLU()
        self.layer2 = nn.Linear(hidden_size, hidden_size // 2)
        self.layer2_act = nn.LeakyReLU()
        self.clf = nn.Linear(hidden_size // 2, 1)
        self.dropout = nn.Dropout(p=dropout)
        
    def forward(self, encoder_outputs, encoder_input_lengths):
        # from stackoverflow (https://stackoverflow.com/questions/50856936/taking-the-last-state-from-bilstm-bigru-in-pytorch)
        # First we unsqueeze seqlengths two times so it has the same number of
        # of dimensions as output_forward
        # (batch_size) -> (1, batch_size, 1)
        lengths = encoder_input_lengths.unsqueeze(0).unsqueeze(2)
        # Then we expand it accordingly
        # (1, batch_size, 1) -> (1, batch_size, hidden_size) 
        lengths = lengths.expand((1, -1, encoder_outputs.size(2)))

        # take only the last state of the encoder for each batch
        last_outputs = torch.gather(encoder_outputs, 0, lengths-1).squeeze()
        # forward pass through hidden layers
        layer1_out = self.layer1_act(self.layer1(self.dropout(last_outputs)))
        layer2_out = self.layer2_act(self.layer2(self.dropout(layer1_out)))
        # compute and return logits
        logits = self.clf(self.dropout(layer2_out)).squeeze()
        return logits

class Predictor(nn.Module):
    """This helper module encapsulates the CRAFT pipeline, defining the logic of passing an input through each consecutive sub-module."""
    def __init__(self, encoder, context_encoder, classifier):
        super(Predictor, self).__init__()
        self.encoder = encoder
        self.context_encoder = context_encoder
        self.classifier = classifier
        
    def forward(self, input_batch, dialog_lengths, dialog_lengths_list, utt_lengths, batch_indices, dialog_indices, batch_size, max_length):
        # Forward input through encoder model
        _, utt_encoder_hidden = self.encoder(input_batch, utt_lengths)
        
        # Convert utterance encoder final states to batched dialogs for use by context encoder
        context_encoder_input = makeContextEncoderInput(utt_encoder_hidden, dialog_lengths_list, batch_size, batch_indices, dialog_indices)
        
        # Forward pass through context encoder
        context_encoder_outputs, context_encoder_hidden = self.context_encoder(context_encoder_input, dialog_lengths)
        
        # Forward pass through classifier to get prediction logits
        logits = self.classifier(context_encoder_outputs, dialog_lengths)
        
        # Apply sigmoid activation
        predictions = F.sigmoid(logits)
        return predictions

def makeContextEncoderInput(utt_encoder_hidden, dialog_lengths, batch_size, batch_indices, dialog_indices):
    """The utterance encoder takes in utterances in combined batches, with no knowledge of which ones go where in which conversation.
       Its output is therefore also unordered. We correct this by using the information computed during tensor conversion to regroup
       the utterance vectors into their proper conversational order."""
    # first, sum the forward and backward encoder states
    utt_encoder_summed = utt_encoder_hidden[-2,:,:] + utt_encoder_hidden[-1,:,:]
    # we now have hidden state of shape [utterance_batch_size, hidden_size]
    # split it into a list of [hidden_size,] x utterance_batch_size
    last_states = [t.squeeze() for t in utt_encoder_summed.split(1, dim=0)]
    
    # create a placeholder list of tensors to group the states by source dialog
    states_dialog_batched = [[None for _ in range(dialog_lengths[i])] for i in range(batch_size)]
    
    # group the states by source dialog
    for hidden_state, batch_idx, dialog_idx in zip(last_states, batch_indices, dialog_indices):
        states_dialog_batched[batch_idx][dialog_idx] = hidden_state
        
    # stack each dialog into a tensor of shape [dialog_length, hidden_size]
    states_dialog_batched = [torch.stack(d) for d in states_dialog_batched]
    
    # finally, condense all the dialog tensors into a single zero-padded tensor
    # of shape [max_dialog_length, batch_size, hidden_size]
    return torch.nn.utils.rnn.pad_sequence(states_dialog_batched)

def evaluateBatch(encoder, context_encoder, predictor, voc, input_batch, dialog_lengths, 
                  dialog_lengths_list, utt_lengths, batch_indices, dialog_indices, batch_size, device, max_length=MAX_LENGTH):
    # Set device options
    input_batch = input_batch.to(device)
    dialog_lengths = dialog_lengths.to(device)
    utt_lengths = utt_lengths.to(device)
    # Predict future attack using predictor
    scores = predictor(input_batch, dialog_lengths, dialog_lengths_list, utt_lengths, batch_indices, dialog_indices, batch_size, max_length)
    predictions = (scores > 0.5).float()
    return predictions, scores


def evaluateDataset(dataset, encoder, context_encoder, predictor, voc, batch_size, device):
    # create a batch iterator for the given data
    batch_iterator = batchIterator(voc, dataset, batch_size, shuffle=False)
    # find out how many iterations we will need to cover the whole dataset
    n_iters = len(dataset) // batch_size + int(len(dataset) % batch_size > 0)
    output_df = {
        "id": [],
        "prediction": [],
        "score": []
    }
    print(f'... running craft on {len(dataset)} sub-conversations')
    for iteration in range(1, n_iters+1):
        batch, batch_dialogs, _, true_batch_size = next(batch_iterator)
        # Extract fields from batch
        input_variable, dialog_lengths, utt_lengths, batch_indices, dialog_indices, labels, convo_ids, target_variable, mask, max_target_len = batch
        dialog_lengths_list = [len(x) for x in batch_dialogs]
        # run the model
        predictions, scores = evaluateBatch(encoder, context_encoder, predictor, voc, input_variable,
                                            dialog_lengths, dialog_lengths_list, utt_lengths, batch_indices, dialog_indices,
                                            true_batch_size, device)

        # format the output as a dataframe (which we can later re-join with the corpus)
        if true_batch_size > 0:
            for i in range(true_batch_size):
                convo_id = convo_ids[i]
                pred = predictions[i].item()
                score = scores[i].item()
                output_df["id"].append(convo_id)
                output_df["prediction"].append(pred)
                output_df["score"].append(score)
                
        # print("Iteration: {}; Percent complete: {:.1f}%".format(iteration, iteration / n_iters * 100))

    return pd.DataFrame(output_df).set_index("id")

print("Loading saved parameters...")
if not (os.path.isfile("model_cmv.tar")):
    print("\tDownloading trained CRAFT_cmv...")
    urlretrieve(MODEL_URL['cmv'], "model_cmv.tar")
    print("\t...Done!")
checkpoint_cmv = torch.load("model_cmv.tar",map_location=torch.device('cpu'))

voc_cmv = loadPrecomputedVoc("cmv", WORD2INDEX_URL['cmv'], INDEX2WORD_URL['cmv'])

# If running in a non-GPU environment, you need to tell PyTorch to convert the parameters to CPU tensor format.
# To do so, replace the previous line with the following:
#checkpoint = torch.load("model.tar", map_location=torch.device('cpu'))
encoder_sd_cmv = checkpoint_cmv['en']
context_sd_cmv = checkpoint_cmv['ctx']
attack_clf_sd_cmv = checkpoint_cmv['atk_clf']
embedding_sd_cmv = checkpoint_cmv['embedding']
voc_cmv.__dict__ = checkpoint_cmv['voc_dict']

print('Building encoders, decoder, and classifier...')
# Initialize word embeddings
embedding_cmv = nn.Embedding(voc_cmv.num_words, hidden_size)
embedding_cmv.load_state_dict(embedding_sd_cmv)

# Initialize utterance and context encoders
encoder_cmv = EncoderRNN(hidden_size, embedding_cmv, encoder_n_layers, dropout)
context_encoder_cmv = ContextEncoderRNN(hidden_size, context_encoder_n_layers, dropout)
encoder_cmv.load_state_dict(encoder_sd_cmv)
context_encoder_cmv.load_state_dict(context_sd_cmv)

# Initialize classifier
attack_clf_cmv = SingleTargetClf(hidden_size, dropout)
attack_clf_cmv.load_state_dict(attack_clf_sd_cmv)

# Tell torch to use GPU. Note that if you are running this notebook in a non-GPU environment, you can change 'cuda' to 'cpu' to get the code to run.
device = torch.device('cpu')

# Use appropriate device
encoder_cmv = encoder_cmv.to(device)
context_encoder_cmv = context_encoder_cmv.to(device)
attack_clf_cmv = attack_clf_cmv.to(device)

print('Models built and ready to go!')

# Set dropout layers to eval mode
encoder_cmv.eval()
context_encoder_cmv.eval()
attack_clf_cmv.eval()

# Initialize the pipeline
predictor_cmv = Predictor(encoder_cmv, context_encoder_cmv, attack_clf_cmv)

def rank_convos(corpus,run_craft=True):
    print(f'corpus has {len(list(corpus.iter_conversations()))} conversations happening accross {len(corpus.utterances)} utterances')
    if run_craft:
        test_pairs_cmv = loadPairs(voc_cmv, corpus, None)
        random.seed(2019)
        forecasts_df_cmv = evaluateDataset(test_pairs_cmv, encoder_cmv, context_encoder_cmv, predictor_cmv, voc_cmv, batch_size, device)

        print('merging results back into corpus')
        for convo in corpus.iter_conversations():
            for utt in convo.iter_utterances():
                if utt.id in forecasts_df_cmv.index:
                    utt.meta['forecast_score_cmv'] = forecasts_df_cmv.loc[utt.id].score
                else:
                    # print(f'did not rank utterance {utt.id}')
                    pass
    else:
        c = 0.
        for convo in corpus.iter_conversations():
            for utt in convo.iter_utterances():
                utt.meta['forecast_score_cmv'] = c
                c += 1.
                    
    return corpus
