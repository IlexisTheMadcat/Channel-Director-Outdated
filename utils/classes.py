
# Lib
from copy import deepcopy
from datetime import datetime
from os import getcwd
from os.path import exists

# Site
from dbl.client import DBLClient
from dbl.errors import DBLException
from discord.ext.commands.bot import Bot as DiscordBot
from discord.ext.commands.context import Context

# Local
from utils.tokens import Tokens


class Globals:
    def __init__(self):
        self.TearingDown = list()
        self.cwd = getcwd()
        self.LoadingUpdate = {"guildID": "bool"}

        # if not exists(f"{self.cwd}\\Serialized\\data.pkl"):  # TODO: All data from Ram's Globals
        #     print("[Unable to load] data.pkl not found. Replace file before shutting down. Saving disabled.")
        #     self.DisableSaving = True
        #     self.VanityAvatars = {"guildID": {"userID":["avatar_url", "previous", "is_blocked"]}}
        #     self.Blacklists = {"authorID": (["channelID"], ["prefix"])}
        #     self.ServerBlacklists = {"guildID": (["channelID"], ["prefix"])}
        #     self.Closets = {"auhthorID": {"closet_name":"closet_url"}}
        #     self.ChangelogCache = None
        #
        # else:
        #     self.DisableSaving = False
        #     with open(f"{self.cwd}\\Serialized\\data.pkl", "rb") as f:
        #         try:
        #             data = Unpickler(f).load()
        #             self.VanityAvatars = data["VanityAvatars"]
        #             self.Blacklists = data["Blacklists"]
        #             self.Closets = data["Closets"]
        #             self.ServerBlacklists = data["ServerBlacklists"]
        #             self.ChangelogCache = data["ChangelogCache"]
        #             print("[] Loaded data.pkl.")
        #         except Exception as e:
        #             self.VanityAvatars = {"guildID": {"userID":["avatar_url", "previous", "is_blocked"]}}
        #             self.Blacklists = {"authorID": (["channelID"], ["prefix"])}
        #             self.ServerBlacklists = {"guildID": (["channelID"], ["prefix"])}
        #             self.Closets = {"auhthorID": {"closet_name": "closet_url"}}
        #             self.ChangelogCache = None
        #             print("[Data Reset] Unpickling Error:", e)


class helper_functions():
    def __init__(self, bot):
        self.bot = bot

    async def convert_to_readable(self, ctx: Context):  # It is advised to use update_directory(ctx) first. 'ctx' must meet the requirements for getting .guild and its directory.
        directory = deepcopy(self.bot.univ.Directories[ctx.guild.id]["tree"])
        
        while True:
            if ctx.guild.id in self.bot.univ.LoadingUpdate:
                await asyncio.sleep(1)
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

    async def convert_to_directory(self, ctx, directory): # This function should be used in an automatic setup. # 'ctx' must meet the requirements for getting .guild. 'directory' is the directory from the unpickled file attached.
        cat = await self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["categoryID"])
        dchannel = await self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["channelID"])

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
                                    await ch.edit(name=f"{yk}-{ch.id}", topic=f"Go back: {dchannel.mention}; Name: {ik}")
                                    
                                elif isinstance(yv, dict):
                                    for zk, zv in directory["root"][ik][xk][yk].items():
                                        if zv is None:
                                            ch = await cat.create_text_channel("finishing creation...")
                                            directory["root"][ik][xk][yk][zk] = ch.id
                                            await ch.edit(name=f"{zk}-{ch.id}", topic=f"Go back: {dchannel.mention}; Name: {ik}")
                                            
                                        elif isinstance(zv, dict):
                                            for ak, av in directory["root"][ik][xk][yk][zk].items():
                                                if av is None:
                                                    ch = await cat.create_text_channel("finishing creation...")
                                                    directory["root"][ik][xk][yk][zk][ak] = ch.id
                                                    await ch.edit(name=f"{ak}-{ch.id}", topic=f"Go back: {dchannel.mention}; Name: {ik}")
            return directory
        else:
            raise ValueError("Invalid dictionary passed.")

    async def update_directory(self, ctx, note=""): # ctx must meet the requirements for acessing .guild and a messagable.
        try:
            dchannel = await self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["channelID"])	
        except discord.errors.NotFound:	
            try:	
                cat = await self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["categoryID"])	
            except discord.errors.NotFound:	
                await ctx.send("You need to set up your directory again.")	
                self.bot.univ.Directories.pop(ctx.guild.id)
                return

            dchannel = await cat.create_text_channel("directory", topic="Managers: Leave this channel on top for easy access. Feel free to move or rename it.")	
            self.bot.univ.Directories[ctx.guild.id]["channelID"] = dchannel.id
            msg = await dchannel.send("Completing repairs...")
            self.bot.univ.Directories[ctx.guild.id]["msgID"] = msg.id
            
        try:	
            msg = await dchannel.fetch_message(self.bot.univ.Directories[ctx.guild.id]["msgID"])	
        except discord.errors.NotFound:	
            msg = await dchannel.send("Completing repairs...")
            self.bot.univ.Directories[ctx.guild.id]["msgID"] = msg.id

        async with dchannel.typing():
            if list(self.bot.univ.Directories[ctx.guild.id]["tree"]["root"].items()) == []:
                msg = await dchannel.fetch_message(self.bot.univ.Directories[ctx.guild.id]["msgID"])
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
                    self.bot.univ.LoadingUpdate[ctx.guild.id] = True
                    for ik, iv in self.bot.univ.Directories[ctx.guild.id]["tree"]["root"].items():
                        if isinstance(iv, int):
                            try:
                                channel = await self.bot.fetch_channel(iv)
                            except discord.NotFound:
                                self.bot.univ.Directories[ctx.guild.id]["tree"]["root"].pop(ik)
                                return False
                            else:
                                message_lines.append(f"**ーー [** {ik} **>>>** ||{channel.mention}||")
                                
                        elif isinstance(iv, dict):
                            message_lines.append(f"**ーー Category: [** {ik} **]**")
                            for xk, xv in self.bot.univ.Directories[ctx.guild.id]["tree"]["root"][ik].items():
                                if isinstance(xv, int):
                                    try:
                                        channel = await self.bot.fetch_channel(xv)
                                    except discord.NotFound:
                                        self.bot.univ.Directories[ctx.guild.id]["tree"]["root"][ik].pop(xk)
                                        return False
                                    else:
                                        message_lines.append(f"**ーーーー [** {xk} **>>>** ||{channel.mention}||")

                                elif isinstance(xv, dict):
                                    message_lines.append(f"**ーーーー Category: [** {xk} **]**")
                                    for yk, yv in self.bot.univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk].items():
                                        if isinstance(yv, int):
                                            try:
                                                channel = await self.bot.fetch_channel(yv)
                                            except discord.NotFound:
                                                self.bot.univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk].pop(yk)
                                                return False
                                            else:
                                                message_lines.append(f"**ーーーーーー [** {yk} **>>>** ||{channel.mention}||")

                                        elif isinstance(yv, dict):
                                            message_lines.append(f"**ーーーーーー Category: [** {yk} **]**")
                                            for zk, zv in self.bot.univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk][yk].items():
                                                if isinstance(zv, int):
                                                    try:
                                                        channel = await self.bot.fetch_channel(zv)
                                                    except discord.NotFound:
                                                        self.bot.univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk][yk].pop(zk)
                                                        return False
                                                    else:
                                                        message_lines.append(f"**ーーーーーーーー [** {zk} **>>>** ||{channel.mention}||")

                                                elif isinstance(zv, dict):
                                                    message_lines.append(f"**ーーーーーーーー Category: [** {zk} **]**")
                                                    for ak, av in self.bot.univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk][yk][zk].items():
                                                        if isinstance(av, int):
                                                            try:
                                                                channel = await self.bot.fetch_channel(av)
                                                            except discord.NotFound:
                                                                self.bot.univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk][yk][zk].pop(ak)
                                                                return False
                                                            else:
                                                                message_lines.append(f"**ーーーーーーーーーー [** {ak} **>>>** ||{channel.mention}||")
                    
                    return True

                while True:
                    dchannel = await self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["channelID"])
                    msg = await dchannel.fetch_message(self.bot.univ.Directories[ctx.guild.id]["msgID"])
                    result = await read()
                    if result is False:
                        message_lines = []
                        continue
                    else:

                        self.bot.univ.LoadingUpdate[ctx.guild.id] = False
                        if list(self.bot.univ.Directories[ctx.guild.id]["tree"]["root"].items()) == []:
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
                                message = await dchannel.fetch_message(self.bot.univ.Directories[ctx.guild.id]["msgID"])
                            except discord.errors.NotFound:
                                message = await dchannel.send("Completing...")
                            else:
                                try:
                                    await message.edit(content=message_full)
                                    await dchannel.send(f"Updated. `{note}`", delete_after=10)
                                    return

                                except discord.HTTPException as e:
                                    await dchannel.send(f":exclamation: The directory message is too large to be edited. A fix will be implemented in the future.\nIf this is not the case, it is likely a network or Discord error. Please try again.\n`Error description: [{e}]`", delete_after=20)
                            return


class Bot(DiscordBot):

    def __init__(self, *args, **kwargs):

        # Backwards patch Globals class for availability to cogs
        self.univ = Globals()
        self.cwd = self.univ.cwd

        # Capture extra meta from init for cogs, former `global`s
        self.debug_mode = kwargs.pop("debug_mode", False)
        self.tz = kwargs.pop("tz", "CST")

        # Attribute for accessing tokens from file
        self.auth = Tokens()

        # Attribute will be filled in `on_ready`
        self.owner: User = None

        super().__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        super().run(self.auth.MWS_BOT_TOKEN, *args, **kwargs)

    def connect_dbl(self, autopost: bool = None):

        print("Connecting DBL with token.")
        try:
            if not self.auth.MWS_DBL_TOKEN:
                raise DBLException
            dbl = DBLClient(self, self.auth.MWS_DBL_TOKEN, autopost=autopost)

        except DBLException:
            self.auth.MWS_DBL_TOKEN = None
            print("\nDBL Login Failed: No token was provided or token provided was invalid.")
            dbl = None

        if dbl:
            self.auth.MWS_DBL_SUCCESS = True
        else:
            self.auth.MWS_DBL_SUCCESS = False

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

        if not exists(f"{self.cwd}\\Serialized\\data.pkl") and not self.univ.DisableSaving:
            self.univ.DisableSaving = True
            print(f"[Unable to save] data.pkl not found. Replace file before shutting down. Saving disabled.")
            return

        if not self.univ.DisableSaving:
            print("Saving...", end="\r")
            with open(f"{self.cwd}\\Serialized\\data.pkl", "wb") as f:
                try:
                    data = {"VanityAvatars": self.univ.VanityAvatars, "Blacklists": self.univ.Blacklists,
                        "Closets": self.univ.Closets, "ServerBlacklists": self.univ.ServerBlacklists,
                        "ChangelogCache": self.univ.ChangelogCache}

                    dump(data, f)
                except Exception as e:
                    print(f"[{time} || Unable to save] Pickle dumping Error:", e)

            self.univ.Inactive = self.univ.Inactive + 1
            print(f"[VPP: {time}] Saved data.")

        await super().logout()
