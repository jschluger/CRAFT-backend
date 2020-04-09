import os
import json
from .block import Block


class Intermediate:
    """ Represents the accumulation of 2 or more revisions' content in a format
    easily convertible to convokit Corpus.

    :param filepath: the location of the Intermediate on disk, if applicable. (Optional)
    :type filepath: str

    :ivar hash_lookup: a dictionary mapping block hashes (the md5 hash of the block's 
    text) to the hash of the next edit of that same block in the case that it was 
    modified in some revision after it was added. An block that has not been edited's hash simply maps to itself.
    :type hash_lookup: dict
    :ivar blocks: a dictionary mapping block hashes (the md5 hash of the block's text)
    to the Block object representing that block.
    :type blocks: dict
    :ivar revisions: a list of tuples describing the revisions that form this Intermediate, 
    where each tuple is (revision's id, list of behaviors of the blocks modified in that revision) 
    e.g. (1234, ["create_section", "add_comment"]) means that the user who submitted revision 1234
    created a new conversation section and added a comment after it.
    :type revisions: list
    :ivar _filepath: the filepath of the Intermediate on disk; where it will be written to
    :type _filepath: str
    """

    def __init__(self, filepath: str = None) -> None:
        if filepath:
            self.load_from_disk(filepath)
        else:
            self.hash_lookup = {}
            self.blocks = {}
            self.revisions = []
            self._filepath = None

    def __str__(self) -> str:
        res = "HASH_LOOKUP---------------------------\n"
        for k, v in self.hash_lookup.items():
            res += (k + ": " + v + "\n")

        res += "BLOCKS--------------------------------\n"
        for k, v in self.blocks.items():
            res += "HASH: " + k + "\n"
            res += str(v)
            res += "---------------------------\n"

        res += "REVISIONS-----------------------------\n"
        for k, v in self.revisions:
            res += str(k) + ": " + str(v) + "\n"
            res += "---------------------------\n"

        return res

    def set_filepath(self, fp: str) -> None:
        self._filepath = fp

    def get_filepath(self) -> str:
        return self._filepath

    def load_from_disk(self, filepath: str) -> None:
        """Loads from a json at filepath the Intermediate data stored in it.

        :return: None
        """
        with open(filepath, "r") as f:
            obj = json.load(f)
            self.hash_lookup = obj["hash_lookup"]
            self.blocks = self._deserialize_blocks(obj["blocks"])
            self.revisions = obj["revisions"]
            self._filepath = filepath

    def write_to_disk(self) -> None:
        """Writes intermediate to self._filepath as a json

        :return: None
        """
        assert(self._filepath is not None)
        with open(self._filepath, "w") as f:
            obj = {}
            obj["hash_lookup"] = self.hash_lookup
            obj["blocks"] = self._serialize_blocks()
            obj["revisions"] = self.revisions
            json.dump(obj, f)

    def get_last_revision_id(self) -> int:
        """Returns the id of last revision that contributed to this Intermediate.

        :return: revision id (int)
        """
        last_revision = self.revisions[-1]
        return last_revision[0]

    def find_ultimate_hash(self, h: str) -> str:
        """Finds the hash of the most recent edit of the block given by h. 
        A block gets a new hash every time its text is edited, but still maintains
        certain metadata about its earlier state. This is meant to look up the most 
        recent edit of a given block.

        :param h: the hash of some block that is in or had been in self.blocks
        :type h: str

        :return: the hash of the most recent block to which h was modified 
        """
        try:
            while self.hash_lookup[h] != h:
                h = self.hash_lookup[h]
            return h
        except KeyError:
            return None

    def compute_reply_hash(self, reply_to_hash: str, reply_to_depth: int, this_depth: int) -> str:
        """Returns the hash of the block to which a block is replying.

        :param reply_to_hash: the hash of the block above the current block
        :type reply_to_hash: str
        :param reply_to_depth: the reply depth of the block above the current block (number of ":" at beginning of text)
        :type reply_to_depth: int
        :param this_depth: the reply depth of the current block (number of ":" at beginning of text)
        :type this_depth: int

        :return: the hash of the block to which the current block is replying
        """
        if this_depth == 0 or reply_to_depth == -1:
            return None
        elif this_depth > reply_to_depth:
            return reply_to_hash
        else:
            while reply_to_depth > this_depth:
                try:
                    # we know for a fact that reply_to_hash is most recent version
                    reply_block = self.blocks[reply_to_hash]
                    reply_to_hash = self.find_ultimate_hash(
                        reply_block.reply_to)
                    reply_to_depth -= 1
                except:
                    # in the case that a high level comment is not stored
                    return None

    def segment_contiguous_blocks(self, reply_chain: list) -> list:
        """Turns a reply chain into a list of sublists, where each sublist contains
        the blocks that form a single utterance (given by the fact that it is a 
        continuous block of one text by one author that is not the conversation's title).

        Ex: the block given by hash "abcd" is a full comment/utterance, and 
        the blocks given by "efgh", "ijkl" are two paragraphs of the same comment/utterance:
        ["abcd", "efgh", "ijkl"] -> [["abcd"], ["efgh", "ijkl"]]

        :param reply_chain: the reply chain
        :type reply_chain: list

        :return: a list of utterance segments, where each utterance segment is a list of constituent blocks 
        """
        i = 0
        last_h = self.find_ultimate_hash(reply_chain[i])
        while not last_h and i < len(reply_chain):
            i += 1
            last_h = self.find_ultimate_hash(reply_chain[i])

        if i == len(reply_chain):
            # Should not happen
            return [[]]

        if len(reply_chain) == i - 1:
            return [[last_h]]

        res = []
        last_user = self.blocks[last_h].user
        contig = [last_h]

        # print("last: ", self.blocks[last_h].root_hash)
        for h in reply_chain[i+1:]:
            this_h = self.find_ultimate_hash(h)

            if this_h is None:
                continue
            # print("this: ", self.blocks[this_h].root_hash)
            this_user = self.blocks[this_h].user
            if this_user == last_user and not self.blocks[last_h].is_header:
                contig.append(this_h)
            else:
                res.append(contig)
                contig = [this_h]
            last_h = this_h
            last_user = this_user
        if len(contig) > 0:
            res.append(contig)
        return res

    def _serialize_blocks(self) -> dict:
        """Converts all blocks from a dict of Block objects to a dict of json-serializable dicts.

        :return: a dictionary mapping block hashes to block dicts.
        """
        res = {}
        for h, b in self.blocks.items():
            block = {}
            block["text"] = b.text
            block["timestamp"] = b.timestamp
            block["user"] = b.user
            block["ingested"] = b.ingested
            block["revisions"] = b.revision_ids
            block["reply_chain"] = b.reply_chain
            block["is_followed"] = b.is_followed
            block["is_header"] = b.is_header
            res[h] = block
        return res

    def _deserialize_blocks(self, blocks: dict) -> dict:
        """Converts all blocks from a dict of dict (from json) objects to a dict of Block objects.

        :param blocks: a dictionary of blocks ingested from json
        :type blocks: dict

        :return: a dictionary mapping block hashes to Block objects
        """
        res = {}
        for h, b in blocks.items():
            block = Block()
            block.text = b["text"]
            block.timestamp = b["timestamp"]
            block.user = b["user"]
            block.ingested = b["ingested"]
            block.revision_ids = b["revisions"]
            block.reply_chain = b["reply_chain"]
            block.is_followed = b["is_followed"]
            block.is_header = b["is_header"]
            res[h] = block
        return res
