from comments import CommentCorpus

cc = CommentCorpus("Guy_Fieri")
for k, v in cc.comment_lookup.items():
    if k == v.root:
        print(k, v.body[:21], v.root)
