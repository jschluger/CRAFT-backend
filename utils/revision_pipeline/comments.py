from .intermediate import Intermediate
from . import helpers
from .pipeline import get_intermediate
import time
import copy


class Comment:
    """ 
    Represents a Wikipedia talk page utterance in PRAW-like format.

    """

    def __init__(self, comment_id: str, text: str, author: str,
                 post: str, time: str, reply_to: str, root: str) -> None:
        self.author = author
        self.id = comment_id
        self.body = text
        self.created_utc = time
        self.parent_id = reply_to
        self.root = root
        self.post = post


class CommentCorpus:
    """
    Interface for dealing with PRAW-style comments.

    """

    def __init__(self, title: str = None):
        self.comment_lookup = {}
        if title:
            accum = get_intermediate(title)
            self.convert_intermediate_to_corpus(accum, title)

    def convert_intermediate_to_corpus(self, accum: Intermediate, title: str) -> None:
        """Generates a CommentCorpus from an Intermediate.

        :param accum: the Intermediate to be converted
        :type accum: Intermediate

        :return: the CommentCorpus generated from accum
        """
        users = {}
        utterances = []
        unknown_len = set()
        complete_utterances = set()
        block_hashes_to_segments = {}
        self.comment_lookup = {}
        for block_hash, block in accum.blocks.items():
            segments = accum.segment_contiguous_blocks(block.reply_chain)
            for seg in segments[:-1]:
                sos = helpers.string_of_seg(seg)
                complete_utterances.add(sos)

            assert(block_hash == segments[-1][-1])
            if not accum.blocks[segments[-1][-1]].is_followed:
                complete_utterances.add(helpers.string_of_seg(segments[-1]))
            block_hashes_to_segments[block_hash] = segments

        for utt in iter(complete_utterances):
            block_hashes = utt.split(" ")
            belongs_to_segment = block_hashes_to_segments[block_hashes[0]]
            first_block = accum.blocks[block_hashes[0]]

            u_id = block_hashes[0]
            u_user = first_block.user
            u_root = accum.find_ultimate_hash(first_block.root_hash)
            u_replyto = self._find_reply_to_from_segment(belongs_to_segment)
            u_timestamp = first_block.timestamp
            u_text = "\n".join([accum.blocks[h].text for h in block_hashes])
            this_comment = Comment(u_id, u_text, u_user,
                                   title, u_timestamp, u_replyto, u_root)
            self.comment_lookup[u_id] = this_comment

        return None

    def comment_ids(self) -> set:
        return set(self.comment_lookup.keys())

    def _find_reply_to_from_segment(self, segment: list) -> str:
        """Helper function. Finds the hash of the comment to which a comment given by the last segment in a list is replying.

        :param segment: a list of block segments produced by Intermediate.segment_continuous_blocks()
        :type segment: list

        :return: the hash of the block to which the last segment in the list is replying.
        """
        if len(segment) == 1:
            return None
        else:
            return segment[-2][0]

    def get_comment(self, comment_id: str) -> Comment:
        return self.comment_lookup.get(comment_id, None)


class CommentGenerator():
    """
    Interface for generator of live Wikipedia Talk page stream
    """

    def __init__(self, topics: list) -> None:
        self.topics = topics
        self.curr_corpora = {}
        self.old_corpora_comment_ids = {}
        print("generating initial", len(self.topics), "corpora")
        for topic in self.topics:
            self.curr_corpora[topic] = CommentCorpus(topic)
            self.old_corpora_comment_ids[topic] = self.curr_corpora[topic].comment_ids(
            )

    def stream(self):
        assert(len(self.topics) > 0)
        while True:
            for topic in self.topics:
                self.old_corpora_comment_ids[topic] = self.curr_corpora[topic].comment_ids(
                )
                self.curr_corpora[topic] = CommentCorpus(topic)
                new_comments = self.curr_corpora[topic].comment_ids(
                ).difference(self.old_corpora_comment_ids[topic])
                if len(new_comments) > 0:
                    yield [(topic, self.curr_corpora[topic].get_comment[c]) for c in new_comments]
            time.sleep(2)
