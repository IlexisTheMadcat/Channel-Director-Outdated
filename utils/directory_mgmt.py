
# Lib
from typing import List
from contextlib import contextmanager
# Site

# Local


def recurse_index(d: dict, indices: List[str]):
    ret = d
    for index in indices:
        ret = ret[index]
    return ret


@contextmanager
def LoadingUpdate_contextmanager(bot, ID: int):
    bot.univ.LoadingUpdate.append(ID)
    try:
        yield None
    finally:
        bot.univ.LoadingUpdate.remove(ID)
