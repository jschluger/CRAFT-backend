class Block:
    """Represents a single edit block as viewable in the revision history window
    on Wikipedia. Most revisions modify several blocks, as usually each paragraph
    constitutes its own block.

    :ivar text: the text contained in the block
    :type text: str
    :ivar timestamp: the time of the revision in which the block was last edited
    :ivar user: the username of the person who last edited the block
    :type user: str
    :ivar ingested: whether this block was added in a revision or just recognized to have been on the page before the revisions ingested
    :type ingested: bool
    :ivar revision_ids: a list of page revisions that edited this block, chronologically
    :type revision_ids: list
    :ivar reply_chain: the list of blocks that this block is in a reply_chain with. Includes blocks before this block that were added in the same revision.
    :type reply_chain: list
    :ivar is_followed: whether this block has another text block following it in the same revision (e.g. if this is the first of two paragraphs added in a revision)
    :type is_followed: bool
    :ivar is_header: whether this block is a signifier of a new header / discussion
    :type is_header: bool
    """

    def __init__(self):
        self.text = None
        self.timestamp = None
        self.user = None
        self.ingested = None
        self.revision_ids = None
        self.reply_chain = None
        self.is_followed = False
        self.is_header = False
        self.root_hash = None

    def __str__(self):
        res = "-----------------------------\n"
        res += "text: " + self.text + "\n"
        res += "timestamp: " + self.timestamp + "\n"
        res += "user: " + (self.user if self.user else "None") + "\n"
        res += "ingested: " + str(self.ingested) + "\n"
        res += "revision_ids: " + str(self.revision_ids) + "\n"
        res += "reply_chain: " + str(self.reply_chain) + "\n"
        res += "is_followed: " + str(self.is_followed) + "\n"
        res += "is_header: " + str(self.is_header) + "\n"
        res += "root_hash: " + self.root_hash + "\n"
        res += "-----------------------------"
        return res
