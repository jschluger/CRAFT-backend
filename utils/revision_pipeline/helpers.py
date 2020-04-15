import hashlib


def compute_md5(s) -> str:
    """Returns the md5 hash of s

    :param s: data to be hashed

    :return: md5 hash of s
    """

    return hashlib.md5(str(s).strip().encode('utf-8')).hexdigest()


def compute_text_depth(text: str) -> int:
    """Returns the Wikipedia reply depth of text, given by the number of ":" characters at its beginning."""
    if len(text) == 0:
        return 0
    d = 0
    while text[d] == ":":
        d += 1
    return d


def is_new_section_text(added_text: str) -> bool:
    """Returns whether added_text marks a new section on Wikipedia."""
    return ((added_text[:3] == "===" and added_text[-3:] == "===") or
            (added_text[:2] == "==" and added_text[-2:] == "==") or
            (added_text[0] == "=" and added_text[-1] == "="))


def is_unedited_tr(all_td: list) -> bool:
    """Returns whether the list of <td> elements in all_td describe an unedited block from one revision to the next."""
    return len(all_td) == 4 and all_td[0] == all_td[2]


def is_new_content_tr(all_td: list) -> bool:
    """Returns whether the list of <td> elements in all_td describe the addition of a block from one revision to the next."""
    return (len(all_td) == 3 and all_td[0]["class"][0] == "diff-empty" and all_td[2]["class"][0] == "diff-addedline")


def is_removal_tr(all_td: list) -> bool:
    """Returns whether the list of <td> elements in all_td describe the removal of a block from one revision to the next."""
    return (len(all_td) == 3 and all_td[1]["class"][0] == "diff-deletedline" and all_td[2]["class"][0] == "diff-empty")


def is_modification_tr(all_td: list) -> bool:
    """Returns whether the list of <td> elements in all_td describe the modification of a block from one revision to the next."""
    return (len(all_td) == 4 and all_td[1]["class"][0] == "diff-deletedline" and all_td[3]["class"][0] == "diff-addedline")


def is_line_number_tr(all_td: list) -> bool:
    """Returns whether the list of <td> elements in all_td describe a line number block from one revision to the next."""
    return (len(all_td) == 2 and all_td[0]["class"][0] == "diff-lineno" and all_td[1]["class"][0] == "diff-lineno")


def is_moved_right_tr(all_td: list) -> bool:
    """Returns whether the list of <td> elements in all_td describes the movement of a block to that position from one revision to the next."""
    return (len(all_td) == 3 and all_td[1].a and all_td[1].a["class"][0] == "mw-diff-movedpara-right")


def is_moved_left_tr(all_td: list) -> bool:
    """Returns whether the list of <td> elements in all_td describes the movement of a block from that position from one revision to the next."""
    return (len(all_td) == 3 and all_td[0].a and all_td[0].a["class"][0] == "mw-diff-movedpara-left")


def string_of_seg(seg: list) -> str:
    """Returns a string formed from the list of segment hashes seg."""
    return ' '.join(seg)
