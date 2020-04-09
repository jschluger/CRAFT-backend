import data
from utils import craft
# from convokit.forecaster.CRAFTModel import CRAFTModel
# CRAFT_model = CRAFTModel(device_type="cpu", model_path="model_cmv.tar")


def rank_convo(i):
    test_pairs = load_convo_pairs(i)
    forcasts = evaluate_convo(test_pairs)
    # forcasts = CRAFT_model.forecast(test_pairs)
    for idx, utt_id in enumerate(forcasts['id']):
        data.CORPUS.get_utterance(
            utt_id).meta['craft_score'] = forcasts['score'][idx]


def wiki_rank_convo(i):
    test_pairs = wiki_load_convo_pairs(i)
    forcasts = evaluate_convo(test_pairs)
    # forcasts = CRAFT_model.forecast(test_pairs)
    for idx, utt_id in enumerate(forcasts['id']):
        data.WIKI_CORPUS.get_utterance(
            utt_id).meta['craft_score'] = forcasts['score'][idx]


def load_convo_pairs(i):
    # get conversation ending in utterance with id i
    utt = data.CORPUS.get_utterance(i)
    convo = [utt]
    pairs = []
    # pairs = {} # if using convokit craft
    while utt.reply_to is not None:
        utt = data.CORPUS.get_utterance(utt.reply_to)
        convo.append(utt)
    convo = convo[::-1]
    dialog = process_dialog(convo)
    for idx in range(0, len(dialog)):
        if dialog[idx]['scored']:
            continue
        reply = ["UNK"]
        label = False
        comment_id = dialog[idx]["id"]
        # gather as context all utterances preceding the reply
        context = [u["tokens"][:(craft.MAX_LENGTH-1)] for u in dialog[:idx+1]]
        pairs.append((context, reply, label, comment_id))
        # pairs[comment_id] = (context, reply, label) # if using convokit craft
    return pairs


def wiki_load_convo_pairs(i):
    # get conversation ending in utterance with id i
    utt = data.WIKI_CORPUS.get_utterance(i)
    convo = [utt]
    pairs = []
    # pairs = {} # if using convokit craft
    while utt.reply_to is not None:
        utt = data.WIKI_CORPUS.get_utterance(utt.reply_to)
        convo.append(utt)
    convo = convo[::-1]
    dialog = process_dialog(convo)
    for idx in range(0, len(dialog)):
        if dialog[idx]['scored']:
            continue
        reply = ["UNK"]
        label = False
        comment_id = dialog[idx]["id"]
        # gather as context all utterances preceding the reply
        context = [u["tokens"][:(craft.MAX_LENGTH-1)] for u in dialog[:idx+1]]
        pairs.append((context, reply, label, comment_id))
        # pairs[comment_id] = (context, reply, label) # if using convokit craft
    return pairs


def process_dialog(convo):
    processed = []
    for utterance in convo:
        tokens = craft.tokenize(utterance.text)
        # replace out-of-vocabulary tokens
        for i in range(len(tokens)):
            if tokens[i] not in craft.voc_cmv.word2index:
                tokens[i] = "UNK"
        processed.append({"tokens": tokens, "is_attack": 0,
                          "id": utterance.id, "scored": 'craft_score' in utterance.meta})
    return processed


def evaluate_convo(pairs):
    return craft.evaluateDataset(pairs, craft.encoder_cmv,
                                 craft.context_encoder_cmv,
                                 craft.predictor_cmv, craft.voc_cmv,
                                 craft.batch_size, craft.device)
