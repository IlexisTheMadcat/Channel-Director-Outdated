# Lib
from asyncio.tasks import sleep
from contextlib import suppress
from copy import deepcopy
from datetime import datetime
from os import getcwd
from os.path import exists
from pickle import dump, Unpickler
from re import match
from typing import List

# Site
from dbl.client import DBLClient
from dbl.errors import DBLException
from discord.channel import TextChannel
from discord.errors import HTTPException, NotFound
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
        """Replaces all channel IDs `int` with `None`"""

        await self.update_directory(ctx=ctx, note=f"Updated to create download file.")
        directory = deepcopy(self.univ.Directories[ctx.guild.id]["tree"])

        def recurse_convert_to_readable(d: dict):
            for key, val in d.items():
                if isinstance(val, int):
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
        self.univ.LoadingUpdate.update({ctx.guild.id: True})
        cat = self.get_channel(self.univ.Directories[ctx.guild.id]["categoryID"])
        chan_directory = self.get_channel(self.univ.Directories[ctx.guild.id]["channelID"])

        async def recurse_convert_to_directory(d: dict, univ: Globals):
            """Recursively create new channels from directory dict"""
            for key, val in d.items():
                if val is None:
                    channel = await cat.create_text_channel("finishing creation...")
                    d[key] = channel.id
                    await channel.edit(
                        name=f"{key}-{channel.id}",
                        topic=f"Go back: {chan_directory.mention}; Name: {key}"
                    )
                    await sleep(0.2)

                elif isinstance(val, dict):
                    await recurse_convert_to_directory(val, univ)

                else:
                    univ.LoadingUpdate.update({ctx.guild.id: False})
                    raise TypeError("Invalid dictionary passed.")

            univ.LoadingUpdate.update({ctx.guild.id: False})

        await recurse_convert_to_directory(directory["root"], self.univ)
        return directory

    async def update_directory(self, ctx, note="..."):
        """"""

        # ctx must meet the requirements for accessing .guild and a Messageable
        self.univ.LoadingUpdate.update({ctx.guild.id: True})

        try:
            chan_directory = self.get_channel(self.univ.Directories[ctx.guild.id]["channelID"])

        except NotFound:
            try:
                cat = self.get_channel(self.univ.Directories[ctx.guild.id]["categoryID"])

            except NotFound:
                self.univ.Directories.pop(ctx.guild.id)
                return await ctx.send("You need to set up your directory again.")

            chan_directory = await cat.create_text_channel(
                "directory",
                topic="Managers: Leave this channel on top for easy access. "
                      "Feel free to move or rename it."
            )

            self.univ.Directories[ctx.guild.id]["channelID"] = chan_directory.id
            msg = await chan_directory.send("Completing repairs...")
            self.univ.Directories[ctx.guild.id]["msgID"] = msg.id

        try:
            msg = await chan_directory.fetch_message(self.univ.Directories[ctx.guild.id]["msgID"])
            self.univ.Directories[ctx.guild.id]["msgID"] = msg.id

        except NotFound:
            msg = await chan_directory.send("Completing repairs...")
            self.univ.Directories[ctx.guild.id]["msgID"] = msg.id

        async with chan_directory.typing():
            if not list(self.univ.Directories[ctx.guild.id]["tree"]["root"].items()):
                await msg.edit(
                    content="This channel will have a directory under it when "
                            "you create a channel using the special command "
                            "that I provide to you.\n"
                            "Also, make sure I have access to all channels "
                            "added.\n"
                            "You are free to move this channel, but it's best "
                            "to leave on top.\n"
                )
                return await chan_directory.send(f"Updated. `{note}`", delete_after=5)

            else:

                def recurse_read(
                        bot: Bot,
                        d: dict,
                        lines: List[str],
                        depth: int = 1,
                        category: str = "Root Category:"
                ):
                    """Recursively walk bot.Directories for guild and generate
                    a list of strings representing the directory message"""

                    d = {k: d[k] for k in sorted(d, key=lambda k: isinstance(d[k], dict))}
                    lines.append(category)

                    for key, val in d.items():

                        if isinstance(val, int):
                            channel = bot.get_channel(val)

                            if channel is None:
                                d.pop(key)
                                return False

                            else:
                                lines.append(f"{'ーー' * depth} **[** {key} **>>>** ||{channel.mention}||")

                        elif isinstance(val, dict):
                            category = f"**{'ーー' * depth} Category: [** {key} **]**"
                            ret = recurse_read(bot, val, lines, depth + 1, category)

                            if not ret:
                                return False

                    return True



                while True:
                    chan_directory = self.get_channel(self.univ.Directories[ctx.guild.id]["channelID"])
                    msg = await chan_directory.fetch_message(self.univ.Directories[ctx.guild.id]["msgID"])

                    message_lines = list()

                    result = recurse_read(self, self.univ.Directories[ctx.guild.id]["tree"]["root"], message_lines)

                    if result is False:
                        continue

                    else:

                        self.univ.LoadingUpdate[ctx.guild.id] = False
                        if not list(self.univ.Directories[ctx.guild.id]["tree"]["root"].items()):
                            await msg.edit(
                                content="This channel will have a directory under it when you create "
                                        "a channel using the special command that I provide to you.\n"
                                        "Also, make sure I have access to all channels added.\n"
                                        "You are free to move this channel, but it's best to leave on top."
                            )
                            await chan_directory.send(f"Updated. `{note}`", delete_after=10)
                            return

                        else:
                            message_full = "\n".join(message_lines)
                            try:
                                message = await chan_directory.fetch_message(
                                    self.univ.Directories[ctx.guild.id]["msgID"]
                                )

                            except NotFound:
                                message = await chan_directory.send("Completing...")

                            try:
                                await message.edit(content=message_full)
                                await chan_directory.send(f"Updated. `{note}`", delete_after=10)
                                return

                            except HTTPException as e:
                                await chan_directory.send(
                                    ":exclamation: The directory message is too large to be edited. "
                                    "A fix will be implemented in the future.\n"
                                    "If this is not the case, it is likely a network or Discord error. "
                                    f"Please try again.\n`Error description: [{e}]`",
                                    delete_after=20
                                )
                            return

        self.univ.LoadingUpdate.update({ctx.guild.id: False})
