
# Lib
from typing import List

# Site

# Local


def recurse_index(d: dict, indices: List[str]):
    ret = d
    for index in indices:
        ret = ret[index]
    return ret
