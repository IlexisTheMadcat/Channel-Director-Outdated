
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
def loadingupdate(bot, g_id: int):
    """
    Prevents Rem from having a mental breakdown when commands are spammed.
    Removes the guild from the list on completion

    :param bot: The Bot class
    :param g_id: The Guild.id to append to the list
    :return: None
    """
    bot.univ.LoadingUpdate.append(g_id)
    try:
        yield None
    finally:
        bot.univ.LoadingUpdate.remove(g_id)


@contextmanager
def usinggui(bot, g_id: int, u_id: int):
    """
    Users using the GUI; Restricts to one GUI action/user at a time
    Removes the user from the list on completion

    :param bot: The Bot class
    :param g_id: The Guild.id that the GUI belongs to.
    :param u_id: The User.id who is using the GUI.
    :return: None
    """

    bot.univ.using_gui.update({g_id: u_id})
    try:
        yield None
    finally:
        bot.univ.using_gui.pop(g_id)
