# Lib
from asyncio.tasks import sleep
from contextlib import suppress
from copy import deepcopy
from datetime import datetime
from os import getcwd
from os.path import exists
from pickle import dump, Unpickler
from random import randint
from re import match
from typing import List, Tuple

# Site
from dbl.client import DBLClient
from dbl.errors import DBLException
from discord import Message
from discord.channel import TextChannel
from discord.errors import HTTPException, NotFound, Forbidden
from discord.ext.commands.bot import Bot as DiscordBot
from discord.ext.commands.context import Context
from discord.ext.commands.converter import IDConverter
from discord.ext.commands.errors import BadArgument
from discord.user import User
from discord.utils import find, get

# Local
from utils.fileinterface import PickleInterface


class Paginator:

    def __init__(
            self,
            page_limit: int = 1000,
            trunc_limit: int = 2000,
            headers: List[str] = None,
            header_extender: str = u'\u200b'
    ):
        self.page_limit = page_limit
        self.trunc_limit = trunc_limit
        self._pages = None
        self._headers = None
        self._header_extender = header_extender
        self.set_headers(headers)

    @property
    def pages(self):
        if self._headers:
            self._extend_headers(len(self._pages))
            headers, self._headers = self._headers, None
            return [
                (headers[i], self._pages[i]) for i in range(len(self._pages))
            ]
        else:
            return self._pages

    def set_headers(self, headers: List[str] = None):
        self._headers = headers

    def set_header_extender(self, header_extender: str = u'\u200b'):
        self._header_extender = header_extender

    def _extend_headers(self, length: int):
        while len(self._headers) < length:
            self._headers.append(self._header_extender)

    def set_trunc_limit(self, limit: int = 2000):
        self.trunc_limit = limit

    def set_page_limit(self, limit: int = 1000):
        self.page_limit = limit

    def paginate(self, value):
        """
        To paginate a string into a list of strings under
        `self.page_limit` characters. Total len of strings
        will not exceed `self.trunc_limit`.
        :param value: string to paginate
        :return list: list of strings under 'page_limit' chars
        """
        spl = str(value).split('\n')
        ret = []
        page = ''
        total = 0
        for i in spl:
            if total + len(page) < self.trunc_limit:
                if (len(page) + len(i)) < self.page_limit:
                    page += '\n{}'.format(i)
                else:
                    if page:
                        total += len(page)
                        ret.append(page)
                    if len(i) > (self.page_limit - 1):
                        tmp = i
                        while len(tmp) > (self.page_limit - 1):
                            if total + len(tmp) < self.trunc_limit:
                                total += len(tmp[:self.page_limit])
                                ret.append(tmp[:self.page_limit])
                                tmp = tmp[self.page_limit:]
                            else:
                                ret.append(tmp[:self.trunc_limit - total])
                                break
                        else:
                            page = tmp
                    else:
                        page = i
            else:
                ret.append(page[:self.trunc_limit - total])
                break
        else:
            ret.append(page)
        self._pages = ret
        return self.pages


class GlobalTextChannelConverter(IDConverter):
    """Converts to a :class:`~discord.TextChannel`.

    Copy of discord.ext.commands.converters.TextChannelConverter,
    Modified to always search global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name
    """

    @staticmethod
    def _get_from_guilds(bot, getter, argument):
        """Copied from discord.ext.commands.converter to prevent
        access to protected attributes inspection error"""
        result = None
        for guild in bot.guilds:
            result = getattr(guild, getter)(argument)
            if result:
                return result
        return result

    async def convert(self, ctx: Context, argument: str) -> TextChannel:
        bot = ctx.bot

        search = self._get_id_match(argument) or match(r'<#([0-9]+)>$', argument)

        if match is None:
            # not a mention
            if ctx.guild:
                result = get(ctx.guild.text_channels, name=argument)
            else:
                def check(c):
                    return isinstance(c, TextChannel) and c.name == argument

                result = find(check, bot.get_all_channels())
        else:
            channel_id = int(search.group(1))
            if ctx.guild:
                result = ctx.guild.get_channel(channel_id)
            else:
                result = self._get_from_guilds(bot, 'get_channel', channel_id)

        if not isinstance(result, TextChannel):
            raise BadArgument('Channel "{}" not found.'.format(argument))

        return result


class Globals:
    def __init__(self):
        self.Inactive = 0
        self.Loops = []
        self.LoadingUpdate = []
        self.Directories = {"guildID": {"catagoryID": 0, "channelID": 0, "msgID": 0, "tree": {}}}
        self.cwd = getcwd()

        if exists(f"{self.cwd}/Serialized/data.pkl"):
            open(f"{self.cwd}/Serialized/data.pkl").close()

        with open(f"{self.cwd}/Serialized/data.pkl", "rb") as f:
            try:
                data = Unpickler(f).load()
                self.Directories = data["Directories"]
                print("#-------------------------------#\n"
                      "[] Loaded data.pkl.\n"
                      "#-------------------------------#\n")
            except Exception as e:
                self.Directories = {"guildID": {"catagoryID": 0, "channelID": 0, "msgID": 0, "tree": {}}}
                print("[Data Reset] Unpickling Error:", e)


class Bot(DiscordBot):

    def __init__(self, *args, **kwargs):

        # Backwards patch Globals class for availability to cogs
        self.univ = Globals()
        self.cwd = self.univ.cwd

        # Capture extra meta from init for cogs, former `global`s
        self.auto_pull = kwargs.pop("auto_pull", True)
        self.debug_mode = kwargs.pop("debug_mode", False)

        # Attribute for accessing tokens from file
        self.auth = PickleInterface(f"{self.cwd}/Serialized/tokens.pkl")

        # Attribute will be filled in `on_ready`
        self.owner: User = kwargs.pop("owner", None)

        super().__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        super().run(self.auth["MWS_BOT_TOKEN"], *args, **kwargs)

    def connect_dbl(self, autopost: bool = True):
        print("#------------ DBL --------------#\n"
              "| Connecting DBL with token.")
        try:
            if not self.auth["MWS_DBL_TOKEN"]:
                raise DBLException
            dbl = DBLClient(self, self.auth["MWS_DBL_TOKEN"], autopost=autopost)

        except DBLException:
            self.auth["MWS_DBL_TOKEN"] = None
            print("| DBL Login Failed: No token was provided or token provided was invalid.")
            dbl = None

        print("#-------------------------------#")

        if dbl:
            self.auth["MWS_DBL_SUCCESS"] = True
        else:
            self.auth["MWS_DBL_SUCCESS"] = False

        return dbl

    async def logout(self):
        hour = str(datetime.now().hour)
        minute = str(datetime.now().minute)
        date = str(str(datetime.now().date().month) + "/" + str(datetime.now().date().day) + "/" + str(
            datetime.now().date().year))
        if len(hour) == 1:
            hour = "0" + hour
        if len(minute) == 1:
            minute = "0" + minute
        time = f"{hour}:{minute}, {date}"

        print("Saving...", end="\r")
        with open(f"{self.cwd}/Serialized/data.pkl", "wb") as f:
            try:
                data = {
                    "Directories": self.univ.Directories
                }

                dump(data, f)
            except Exception as e:
                print(f"[{time} || Unable to save] Pickle dumping Error:", e)

        print(f"[CDR: {time}] Saved data and logging out...")

        for x_loop in self.univ.Loops:
            x_loop.cancel()

        with suppress(RuntimeError, RuntimeWarning):
            await super().logout()

    # It is advised to use update_directory(ctx) first.
    # 'ctx' must meet the requirements for getting .guild and its directory.
    async def convert_to_readable(self, ctx: Context):
        """Replaces all channel IDs `tuple` with `None`"""

        await self.update_directory(ctx=ctx, note=f"Updated to create download file.")
        directory = deepcopy(self.univ.Directories[ctx.guild.id]["tree"])

        def recurse_convert_to_readable(d: dict):
            for key, val in d.items():
                if isinstance(val, tuple):
                    d[key] = None
                elif isinstance(val, dict):
                    recurse_convert_to_readable(d[key])
                else:
                    raise ValueError("Invalid directory dictionary passed.")

        recurse_convert_to_readable(directory)
        return directory

    async def convert_to_directory(self, ctx: Context, directory: dict):
        """Create new channels for directory"""

        # This method should be used in an automatic setup.
        # 'ctx' must meet the requirements for getting .guild.
        # 'directory' is the directory from the unpickled file attached.

        cat = self.get_channel(self.univ.Directories[ctx.guild.id]["categoryID"])
        directory_ch = self.get_channel(self.univ.Directories[ctx.guild.id]["channelID"])

        async def recurse_convert_to_directory(d: dict, univ: Globals):
            """Recursively create new channels from directory dict"""

            for key, val in d.items():
                if val is None:
                    channel = await cat.create_text_channel("finishing creation...")
                    d[key] = (channel.id, False)
                    await channel.edit(
                        name=f"{key}-{channel.id}",
                        topic=f"Go back: {directory_ch.mention}; Name: {key}"
                    )
                    await sleep(0.2)

                elif isinstance(val, dict):
                    await recurse_convert_to_directory(val, univ)

                else:
                    raise TypeError("Invalid dictionary passed.")

        await recurse_convert_to_directory(directory["root"], self.univ)
        return directory

    def recurse_read(
            self,
            d: dict,
            lines: List[str],
            depth: int = 1,
            category: str = "Root Category:",
            preview: bool = False
    ):
        """Recursively walk bot.Directories for guild and generate
        a list of strings representing the directory message"""

        d = {k: d[k] for k in sorted(d, key=lambda k: isinstance(d[k], dict))}
        lines.append(category)

        for key, val in d.items():
            if isinstance(val, int):  # Retro-patching
                d[key] = Tuple[(val, False)]

            if isinstance(val, tuple) and not preview:
                channel = self.get_channel(val[0])

                if channel is None:
                    d.pop(key)
                    return d

                else:
                    if val[1]:
                        lines.append(f"{'ーー' * depth} **[i] [** {key} **>>>** ||{channel.mention}||")
                    else:
                        lines.append(f"{'ーー' * depth} **[** {key} **>>>** ||{channel.mention}||")

            elif val is None and preview:
                lines.append(f"{'ーー' * depth} **[** {key} **>>>** ||{key.lower().replace(' ', '-')}-000000000000000000||")

            elif isinstance(val, dict) and not preview:
                category = f"**{'ーー' * depth} Category: [** {key} **]**"
                ret = self.recurse_read(val, lines, depth + 1, category)

                if isinstance(ret, dict):
                    d[key] = ret
                    return d

            elif isinstance(val, dict) and preview:
                category = f"**{'ーー' * depth} Category: [** {key} **]**"
                ret = self.recurse_read(val, lines, depth + 1, category, preview=True)

                if isinstance(ret, dict):
                    d[key] = ret
                    return d

        return True

    async def update_directory(self, ctx, note="..."):
        """Update the directory associated with a guild"""
        if ctx.guild.id not in self.univ.Directories:
            return

        # ctx must meet the requirements for accessing .guild and a Messageable

        directory_cat = self.get_channel(self.univ.Directories[ctx.guild.id]["categoryID"])
        directory_ch = self.get_channel(self.univ.Directories[ctx.guild.id]["channelID"])

        if not directory_cat:
            directory_cat = await ctx.guild.create_category_channel(name="Directory Archive")
            self.univ.Directories[ctx.guild.id]["categoryID"] = directory_cat.id

        if not directory_ch:
            directory_ch = await directory_cat.create_text_channel(
                name="directory",
                topic="Managers: Leave this channel on top for easy access. "
                      "Feel free to move or rename it."
            )
            self.univ.Directories[ctx.guild.id]["channelID"] = directory_ch.id
        else:
            await directory_ch.edit(category=directory_cat)

        try:
            directory_msg = await directory_ch.fetch_message(self.univ.Directories[ctx.guild.id]["msgID"])
        except NotFound:
            directory_msg = await directory_ch.send("Completing repairs...")
            self.univ.Directories[ctx.guild.id]["msgID"] = directory_msg.id

        async with directory_ch.typing():
            await sleep(1)
            if not list(self.univ.Directories[ctx.guild.id]["tree"]["root"].items()):
                await sleep(2)
                await directory_msg.edit(
                    content="This channel will have a directory under it when "
                            "you create a channel using the special command "
                            "that I provide to you.\n"
                            "Also, make sure I have access to all channels added.\n"
                            "You are free to move this channel, but it's best "
                            "to leave on top.\n"
                )
                return await directory_ch.send(f"Updated. `{note}`", delete_after=5)

            else:

                while True:
                    message_lines = list()

                    result = self.recurse_read(self.univ.Directories[ctx.guild.id]["tree"]["root"], message_lines)

                    if isinstance(result, dict):
                        self.univ.Directories[ctx.guild.id]["tree"]["root"] = result
                        continue

                    else:
                        if not list(self.univ.Directories[ctx.guild.id]["tree"]["root"].items()):
                            await directory_msg.edit(
                                content="This channel will have a directory under it when you create "
                                        "a channel using the special command that I provide to you.\n"
                                        "Also, make sure I have access to all channels added.\n"
                                        "You are free to move this channel, but it's best to leave on top."
                            )
                            await directory_ch.send(f"Updated. `{note}`", delete_after=10)
                            return

                        else:
                            message_full = "\n".join(message_lines)
                            try:
                                await directory_msg.edit(content=message_full)
                                await directory_ch.send(f"Updated. `{note}`", delete_after=10)
                                return

                            except HTTPException as e:
                                await directory_ch.send(
                                    ":exclamation: The directory message is too large to be edited. "
                                    "A fix will be implemented in the future.\n"
                                    "If this is not the case, it is likely a network or Discord error. "
                                    f"Please try again.\n`Error description: [{e}]`",
                                    delete_after=30
                                )
                            return


class GroupMessage:
    """
    Creates a message group that can be edited.
    This is intended for use with large navigation panels or displays in text
    that require editing frequently. Recommended to use in a locked channel.
    Do not delete any messages in a message group or it's edit function will raise a NotFound exception.
    """

    def __init__(self, channel: TextChannel, max_chars_per: int = 2000, resolution=5):
        # message_group is a list of MESSAGE IDs
        # resolution is the number of messages to manage in a group
        #   if _object in `group_edit` is larger than the total size (max_chars_per*resolution),
        #   ValueError is raised.

        self.max_chars_per = max_chars_per
        self.channel = channel
        self.resolution = resolution

        self.message_group: List[int] = list()

    async def setup(self):
        """ Run this coroutine immediately after creating the GroupMessage instance. """
        if self.max_chars_per <= 0:
            raise ValueError("max_characters cannot be 0 or less.")

        elif self.max_chars_per >= 2000:
            raise ValueError("max_characters cannot be 2000 or more.")

        if self.resolution <= 0:
            raise ValueError("resolution cannot be 0 or less.")

        elif self.resolution >= 20:
            raise ValueError("resolution cannot be 20 or more.")

        self.message_group = list()

        for i in range(self.resolution):
            msg = await self.channel.send("||`!! --------------- !! Do Not Delete !! --------------- !!`||")
            self.message_group.append(msg.id)

    async def group_edit(self, _object):
        """
        Edit the messages in the group instantiated with `setup`
        """

        if not self.message_group:
            raise ValueError("You need to run the `setup` function first.")

        _object = str(_object)
        message_strs = list()

        seeker_sp = 0  # Startpoint
        seeker_ep = self.max_chars_per  # Endpoint
        seeker_max = len(_object)  # Maximun distance to render

        if len(_object) > self.resolution*self.max_chars_per:
            raise ValueError("The value passed is too large to edit the current resolution of messages.\n"
                             "To create a larger message group, create a new instance with a larger resolution.")

        while seeker_sp < seeker_max:
            message_strs.append(_object[seeker_sp:seeker_ep])  # TODO: Find a way to find the nearest `\n` at the split point to make it cleaner
            seeker_sp = seeker_sp + self.max_chars_per
            seeker_ep = seeker_ep + self.max_chars_per

        for ind in range(self.resolution):
            try:
                msg = await self.channel.fetch_message(self.message_group[ind])
            except NotFound:  # Catch the exception to raise it with a new description
                raise IndexError("A message in the message group has been deleted by a user.\n"
                                 "You need to recreate the instance.")

            try:
                await msg.edit(content=message_strs[ind])
            except IndexError:
                await msg.edit(content="||`!! --------------- !! Do Not Delete !! --------------- !!`||")
