# Lib
from typing import List
from copy import deepcopy
from asyncio import sleep
from contextlib import suppress
from datetime import datetime
from os import getcwd
from os.path import exists
from pickle import dump, Unpickler
from re import match

# Site
from dbl.client import DBLClient
from dbl.errors import DBLException
from discord.errors import NotFound, HTTPException
from discord.channel import TextChannel
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
        self.LoadingUpdate = {}
        self.TearingDown = []
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
        self.tz = kwargs.pop("tz", "UTC")
        self.command_prefix = kwargs.pop("commands_prefix", ":>")

        # Attribute for accessing tokens from file
        self.auth = PickleInterface(f"{self.cwd}/Serialized/tokens.pkl")

        # Attribute will be filled in `on_ready`
        self.owner: User = kwargs.pop("owner", None)

        super().__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        super().run(self.auth["MWS_BOT_TOKEN"], *args, **kwargs)

    def connect_dbl(self, autopost: bool = None):

        print("Connecting DBL with token.")
        try:
            if not self.auth["MWS_DBL_TOKEN"]:
                raise DBLException
            dbl = DBLClient(self, self.auth["MWS_DBL_TOKEN"], autopost=autopost)

        except DBLException:
            self.auth["MWS_DBL_TOKEN"] = None
            print("\nDBL Login Failed: No token was provided or token provided was invalid.")
            dbl = None

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

    async def convert_to_readable(self, ctx):  # It is advised to use update_directory(ctx) first. 'ctx' must meet the requirements for getting .guild and its directory.
        directory = deepcopy(self.univ.Directories[ctx.guild.id]["tree"])

        while True:
            if ctx.guild.id in self.univ.LoadingUpdate and self.univ.LoadingUpdate[ctx.guild.id]:
                await sleep(1)
            else:
                break

        if isinstance(directory, dict):
            for ik, iv in directory["root"].items():
                if isinstance(iv, int):
                    directory["root"][ik] = None
                elif isinstance(iv, dict):
                    for xk, xv in directory["root"][ik].items():
                        if isinstance(xv, int):
                            directory["root"][ik][xk] = None
                        elif isinstance(xv, dict):
                            for yk, yv in directory["root"][ik][xk].items():
                                if isinstance(yv, int):
                                    directory["root"][ik][xk][yk] = None
                                elif isinstance(yv, dict):
                                    for zk, zv in directory["root"][ik][xk][yk].items():
                                        if isinstance(zv, int):
                                            directory["root"][ik][xk][yk][zk] = None
                                        elif isinstance(zv, dict):
                                            for ak, av in directory["root"][ik][xk][yk][zk].items():
                                                if isinstance(av, int):
                                                    directory["root"][ik][xk][yk][zk][ak] = None
            return directory
        else:
            raise ValueError("Invalid directory dictionary passed.")

    async def convert_to_directory(self, ctx, directory: dict):
        # This function should be used in an automatic setup.
        # 'ctx' must meet the requirements for getting .guild. 'directory' is the directory from the unpickled file attached.
        self.univ.LoadingUpdate.update({ctx.guild.id: True})
        cat = self.get_channel(self.univ.Directories[ctx.guild.id]["categoryID"])
        dchannel = self.get_channel(self.univ.Directories[ctx.guild.id]["channelID"])

        if isinstance(directory, dict):
            for ik, iv in directory["root"].items():
                if iv is None:
                    ch = await cat.create_text_channel("finishing creation...")
                    directory["root"][ik] = ch.id
                    await ch.edit(name=f"{ik}-{ch.id}", topic=f"Go back: {dchannel.mention}; Name: {ik}")

                elif isinstance(iv, dict):
                    for xk, xv in directory["root"][ik].items():
                        if xv is None:
                            ch = await cat.create_text_channel("finishing creation...")
                            directory["root"][ik][xk] = ch.id
                            await ch.edit(name=f"{xk}-{ch.id}", topic=f"Go back: {dchannel.mention}; Name: {ik}")

                        elif isinstance(xv, dict):
                            for yk, yv in directory["root"][ik][xk].items():
                                if yv is None:
                                    ch = await cat.create_text_channel("finishing creation...")
                                    directory["root"][ik][xk][yk] = ch.id
                                    await ch.edit(name=f"{yk}-{ch.id}",
                                                  topic=f"Go back: {dchannel.mention}; Name: {ik}")

                                elif isinstance(yv, dict):
                                    for zk, zv in directory["root"][ik][xk][yk].items():
                                        if zv is None:
                                            ch = await cat.create_text_channel("finishing creation...")
                                            directory["root"][ik][xk][yk][zk] = ch.id
                                            await ch.edit(name=f"{zk}-{ch.id}",
                                                          topic=f"Go back: {dchannel.mention}; Name: {ik}")

                                        elif isinstance(zv, dict):
                                            for ak, av in directory["root"][ik][xk][yk][zk].items():
                                                if av is None:
                                                    ch = await cat.create_text_channel("finishing creation...")
                                                    directory["root"][ik][xk][yk][zk][ak] = ch.id
                                                    await ch.edit(name=f"{ak}-{ch.id}",
                                                                  topic=f"Go back: {dchannel.mention}; Name: {ik}")
            self.univ.LoadingUpdate.update({ctx.guild.id: False})
            return directory
        else:
            self.univ.LoadingUpdate.update({ctx.guild.id: False})
            raise TypeError("Invalid dictionary passed.")

    async def update_directory(self, ctx, note=""):  # ctx must meet the requirements for accessing .guild and a Messagable.
        self.univ.LoadingUpdate.update({ctx.guild.id: True})
        try:
            dchannel = self.get_channel(self.univ.Directories[ctx.guild.id]["channelID"])
        except NotFound:
            try:
                cat = self.get_channel(self.univ.Directories[ctx.guild.id]["categoryID"])
            except NotFound:
                await ctx.send("You need to set up your directory again.")
                self.univ.Directories.pop(ctx.guild.id)
                return

            dchannel = await cat.create_text_channel("directory", topic="Managers: Leave this channel on top for easy access. Feel free to move or rename it.")
            self.univ.Directories[ctx.guild.id]["channelID"] = dchannel.id
            msg = await dchannel.send("Completing repairs...")
            self.univ.Directories[ctx.guild.id]["msgID"] = msg.id

        try:
            msg = await dchannel.fetch_message(self.univ.Directories[ctx.guild.id]["msgID"])
        except NotFound:
            msg = await dchannel.send("Completing repairs...")
            self.univ.Directories[ctx.guild.id]["msgID"] = msg.id

        async with dchannel.typing():
            if not list(self.univ.Directories[ctx.guild.id]["tree"]["root"].items()):
                msg = await dchannel.fetch_message(self.univ.Directories[ctx.guild.id]["msgID"])
                await msg.edit(content="""
This channel will have a directory under it when you create a channel using the special command that I provide to you.
Also, make sure I have access to all channels added.
You are free to move this channel, but it's best to leave on top.
""")
                await dchannel.send(f"Updated. `{note}`", delete_after=5)
                return

            else:
                message_lines = []

                async def read():
                    message_lines.append("Root Category:")
                    self.univ.LoadingUpdate[ctx.guild.id] = True
                    for ik, iv in self.univ.Directories[ctx.guild.id]["tree"]["root"].items():
                        if isinstance(iv, int):
                            channel = self.get_channel(iv)
                            if channel is None:
                                self.univ.Directories[ctx.guild.id]["tree"]["root"].pop(ik)
                                return False
                            else:
                                message_lines.append(f"ーー **[** {ik} **>>>** ||{channel.mention}||")

                        elif isinstance(iv, dict):
                            message_lines.append(f"**ーー Category: [** {ik} **]**")
                            for xk, xv in self.univ.Directories[ctx.guild.id]["tree"]["root"][ik].items():
                                if isinstance(xv, int):
                                    channel = self.get_channel(xv)
                                    if channel is None:
                                        self.univ.Directories[ctx.guild.id]["tree"]["root"][ik].pop(xk)
                                        return False
                                    else:
                                        message_lines.append(f"ーーーー **[** {xk} **>>>** ||{channel.mention}||")

                                elif isinstance(xv, dict):
                                    message_lines.append(f"**ーーーー Category: [** {xk} **]**")
                                    for yk, yv in self.univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk].items():
                                        if isinstance(yv, int):
                                            channel = self.get_channel(yv)
                                            if channel is None:
                                                self.univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk].pop(yk)
                                                return False
                                            else:
                                                message_lines.append(f"ーーーーーー **[** {yk} **>>>** ||{channel.mention}||")

                                        elif isinstance(yv, dict):
                                            message_lines.append(f"**ーーーーーー Category: [** {yk} **]**")
                                            for zk, zv in self.univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk][yk].items():
                                                if isinstance(zv, int):
                                                    channel = self.get_channel(zv)
                                                    if channel is None:
                                                        self.univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk][yk].pop(zk)
                                                        return False
                                                    else:
                                                        message_lines.append(f"ーーーーーーーー **[** {zk} **>>>** ||{channel.mention}||")

                                                elif isinstance(zv, dict):
                                                    message_lines.append(f"**ーーーーーーーー Category: [** {zk} **]**")
                                                    for ak, av in self.univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk][yk][zk].items():
                                                        if isinstance(av, int):
                                                            channel = self.get_channel(av)
                                                            if channel is None:
                                                                self.univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk][yk][zk].pop(ak)
                                                                return False
                                                            else:
                                                                message_lines.append(f"ーーーーーーーーーー **[** {ak} **>>>** ||{channel.mention}||")

                    return True

                while True:
                    dchannel = self.get_channel(self.univ.Directories[ctx.guild.id]["channelID"])
                    msg = await dchannel.fetch_message(self.univ.Directories[ctx.guild.id]["msgID"])
                    result = await read()
                    if result is False:
                        message_lines = []
                        continue
                    else:

                        self.univ.LoadingUpdate[ctx.guild.id] = False
                        if not list(self.univ.Directories[ctx.guild.id]["tree"]["root"].items()):
                            await msg.edit(content="""
This channel will have a directory under it when you create a channel using the special command that I provide to you.
Also, make sure I have access to all channels added.
You are free to move this channel, but it's best to leave on top.
""")
                            await dchannel.send(f"Updated. `{note}`", delete_after=10)
                            return

                        else:
                            message_full = "\n".join(message_lines)
                            try:
                                message = await dchannel.fetch_message(self.univ.Directories[ctx.guild.id]["msgID"])
                            except NotFound:
                                message = await dchannel.send("Completing...")

                            try:
                                await message.edit(content=message_full)
                                await dchannel.send(f"Updated. `{note}`", delete_after=10)
                                return

                            except HTTPException as e:
                                await dchannel.send(
                                    ":exclamation: The directory message is too large to be edited. "
                                    "A fix will be implemented in the future.\n"
                                    "If this is not the case, it is likely a network or Discord error. "
                                    f"Please try again.\n`Error description: [{e}]`",
                                    delete_after=20)
                            return

        self.univ.LoadingUpdate.update({ctx.guild.id: False})

# class Navigator:
#     def __init__(self, bot):
#         self.bot = bot
#
#     @staticmethod
#     async def compile_and_send(self, ctx: Context, **items: {str: str}):  # **items is a dict of str("title"):str("Data")
#         above = list([str()])
#         selected = str()
#         below = list([str()])
