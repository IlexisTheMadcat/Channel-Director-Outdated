
#Lib
import os
from asyncio import TimeoutError, sleep
from pickle import Unpickler, dump

#Site
from discord import File
from discord.ext import commands
from discord.ext.commands.cog import Cog
from discord.ext.commands.context import Context
from discord.ext.commands.core import bot_has_permissions, command, has_permissions
from discord.errors import NotFound

# Local
from utils.classes import Bot


class Commands(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.bot.remove_command("help")

    @command(name="setup", aliases=["su"])
    @bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True, manage_roles=True)
    @has_permissions(manage_channels=True, manage_guild=True)
    async def setup_directory(self, ctx: Context):
        if not ctx.guild:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in self.bot.univ.Directories.keys():
            msg = await ctx.send("You already have a directory tree set up. Continue anyway?\nReact with :white_check_mark: (within 30 seconds) to continue the setup.\n`[  ]`")
        else:
            msg = await ctx.send("""
This setup will create a new catagory that you can edit, but you should never delete it. This may mess me up big time!
The category is used by the bot to identify it as a storage system for the channels.

The entire process is handled by me so, mind your manners, please.
React with :white_check_mark: (within 30 seconds) to continue the setup.
`[  ]`
""")

        def check(reaction, user):
            return str(reaction.emoji) == "✅" and user == ctx.author and reaction.message.id == msg.id
        
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30, check=check)
        except TimeoutError:
            await msg.delete()
        else:
            await reaction.remove(user)
            if ctx.guild.id in self.bot.univ.Directories.keys():
                await msg.edit(content="""
You already have a directory tree set up. Continue anyway?
React with :white_check_mark: (within 30 seconds) to continue the setup.\n`[✅]`
""")
            else:
                await msg.edit(content="""
This setup will create a new catagory that you can edit, but you should never delete it. This may mess me up big time!
The category is used by the bot to identify it as a storage system for the channels.

The entire process is handled by me so, mind your manners, please.
React with :white_check_mark: (within 30 seconds) to continue the setup.
`[✅]`
""")
            await sleep(2)
            if ctx.guild.id in self.bot.univ.Directories.keys():
                await msg.edit(content="Note: Your old channels will not be deleted, but the old directory channel will not be kept updated or managed anymore.")
                self.bot.univ.Directories.pop(ctx.guild.id)
                await sleep(5)

            if ctx.guild.id not in self.bot.univ.Directories.keys():
                if ctx.message.attachments != []:
                    file = None
                    for i in ctx.message.attachments:
                        if i.filename == f"cdr_directory.pkl":
                            file = i
                            break

                    await msg.edit(content="You've attached a valid file to your message. Do you want to attempt to load it?\nReact with :white_check_mark: (within 10 seconds) to continue the setup.\n`[  ]`")
                    def check(reaction, user):
                        return str(reaction.emoji) == "✅" and user.id == ctx.author.id and reaction.message.id == msg.id
                    
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=10, check=check)
                    except TimeoutError:
                        await msg.delete()
                        return
                    else:
                        await reaction.remove(user)
                        await msg.edit(content="You've attached a valid file to your message. Do you want to attempt to load it?\nReact with :white_check_mark: (within 10 seconds) to continue the setup.\n`[✅]`")
                        await sleep(2)

                        self.bot.univ.LoadingUpdate.update({ctx.guild.id:True})
                        await msg.edit(content="Setting up with attached file...")

                        file = await file.save(f"{self.bot.cwd}\\Workspace\\incoming.pkl")
                        with open(f"{self.bot.cwd}\\Workspace\\incoming.pkl", "rb") as f:
                            tree = Unpickler(f).load()

                        os.remove(f"{self.bot.cwd}\\Workspace\\incoming.pkl")

                        cat = await ctx.guild.create_category("CDR: Directories (Bot Managed)")
                        directory = await cat.create_text_channel("directory", topic="Managers: Leave this channel on top for easy access. Also do not delete it.")
                        
                        await directory.set_permissions(ctx.guild.default_role, send_messages=False)
                        member_self = await ctx.guild.fetch_member(self.bot.user.id)
                        await directory.set_permissions(member_self, send_messages=True)

                        dmessage = await directory.send("Adding channels...")

                        self.bot.univ.Directories.update({ctx.guild.id:{"categoryID":cat.id, "channelID":directory.id, "msgID":dmessage.id, "tree":tree}})

                        try:
                            tree = await self.convert_to_directory(ctx, tree)
                        except TypeError:
                            await msg.edit(content="The setup failed because the file is either changed, corrupted, or outdated.")
                            return
                        else:
                            await self.update_directory(ctx, note="Finished automated setup.")
                            await msg.edit(content=f"Finished setup. Get to the directory here: {directory.mention}")

                        self.bot.univ.LoadingUpdate.update({ctx.guild.id:False})
                else:
                    await msg.edit(content="Setting up now...")
                    cat = await ctx.guild.create_category("CDR: Directories (Bot Managed)")
                    directory = await cat.create_text_channel("directory", topic="Managers: Leave this channel on top for easy access. Also do not delete it.")
                    
                    await directory.set_permissions(ctx.guild.default_role, send_messages=False)
                    member_self = await ctx.guild.fetch_member(self.bot.user.id)
                    await directory.set_permissions(member_self, send_messages=True)

                    dmessage = await directory.send("This channel will have a directory under it when you create a channel using the special command that I provide to you.\nAlso, make sure I have access to all channels added.\nYou are free to move this channel, but it's best to leave on top.")
                    await msg.edit(content=f"Finished setup. Get to the directory here: {directory.mention}")

                    self.bot.univ.Directories.update({ctx.guild.id:{"categoryID":cat.id, "channelID":directory.id, "msgID":dmessage.id, "tree":{"root":{}}}})
                
     
    @command(name="teardown", aliases=["td"])
    @bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True)
    @has_permissions(manage_channels=True, manage_guild=True)
    async def teardown_directory(self, ctx: Context, categoryID: int = 0):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return

        if categoryID == 0:    
            if ctx.guild.id in self.bot.univ.Directories.keys():
                if ctx.channel.id == self.bot.univ.Directories[ctx.guild.id]["channelID"]:
                    await ctx.send("You can't do that here!", delete_after=5)
                    return

                msg = await ctx.send("Are you sure? React with :white_check_mark: (within 20 seconds) to continue.\nIf you want to, you can save your directory first using the `save_directory` command.\n`[  ]`")
                def check(reaction, user):
                    return str(reaction.emoji) == "✅" and user.id == ctx.author.id and reaction.message.id == msg.id
                
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=10, check=check)
                except TimeoutError:
                    await msg.delete()
                else:
                    await reaction.remove(user)
                    await msg.edit(content="Are you sure? React with :white_check_mark: (within 20 seconds) to continue.\nIf you want to, you can save your directory first using the `save_directory` command.\n`[✅]`")
                    await sleep(2)
                    await msg.edit(content="Tearing down...")
                    self.bot.univ.TearingDown.append(ctx.guild.id)
                    try:
                        category = await self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["categoryID"])
                    except NotFound:
                        await msg.edit(content="I couldn't find the category for the channels.")
                        self.bot.univ.Directories.pop(ctx.guild.id)
                        self.bot.univ.TearingDown.remove(ctx.guild.id)
                        return

                    for i in category.channels:
                        await i.delete()

                    await category.delete()

                    self.bot.univ.Directories.pop(ctx.guild.id)
                    self.bot.univ.TearingDown.remove(ctx.guild.id)
                    await msg.edit(content="Teardown complete.")
            else:
                await ctx.send("You don't have a directory to tear down.")
        else:
            if ctx.guild.id in self.bot.univ.Directories.keys() and ctx.channel.id == self.bot.univ.Directories[ctx.guild.id]["channelID"]:
                await ctx.send("You can't do that here!", delete_after=5)
                return
            
            if ctx.guild.id in self.bot.univ.Directories.keys() and categoryID == self.bot.univ.Directories[ctx.guild.id]["categoryID"]:
                await ctx.send("You cannot specify the external category used for the directory. In that case, don't specify any ID.", delete_after=5)
                return

            try:
                category = await self.bot.fetch_channel(categoryID)
            except NotFound:
                await ctx.send("No category with that ID exists.")
            else:
                if not categoryID in [guild.id for guild in ctx.guild.channels]:
                    await ctx.send("That category does exist, but it isn't in your server. Why would I let you do that? Spoiled prankster.")
                    return
    
            msg = await ctx.send("Are you sure? React with :white_check_mark: (within 20 seconds) to continue.\nConfirm: You are deleting an external category.\n`[  ]`")
            def check(reaction, user):
                return str(reaction.emoji) == "✅" and user == ctx.author and reaction.message.id == msg.id
            
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=10, check=check)
            except TimeoutError:
                await msg.delete()
            else:
                await reaction.remove(user)
                await msg.edit(content="Are you sure? React with :white_check_mark: (within 20 seconds) to continue.\nConfirm: You are deleting an external category.\n`[✅]`")
                await sleep(2)
                await msg.edit(content="Tearing down external category...")
                self.bot.univ.TearingDown.append(ctx.guild.id)
                
                for i in category.channels:
                    await i.delete()

                await category.delete()

                self.bot.univ.TearingDown.remove(ctx.guild.id)
                await msg.edit(content="Teardown complete. Note that imported channels from that directory will no longer appear in the directory if you have it set up.")
                if ctx.guild.id in self.bot.univ.Directories.keys():
                    await self.update_directory(ctx, note="External category deletion; Imported channels from that category now removed.")

     
    @command(aliases=["new_ch"])
    @bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True)
    @has_permissions(manage_channels=True)
    async def create_channel(self, ctx: Context, directory: str, name: str):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in self.bot.univ.Directories.keys():
            if ctx.channel.id == self.bot.univ.Directories[ctx.guild.id]["channelID"]:
                await ctx.message.delete()
                if ctx.guild.id in self.bot.univ.LoadingUpdate.keys():
                    if self.bot.univ.LoadingUpdate[ctx.guild.id] == True:
                        await ctx.send("The directory is being updated at the moment. Try again in a few seconds.", delete_after=10)
                        return
                
                if len(name) > 50:
                    await ctx.send("\"name\" cannot be greater than 50 characters long.", delete_after=5)
                    return
                
                d = directory.split("//")
                if len(d) > 5:
                    await ctx.send("You cannot create a channel in a directory deeper than 5.", delete_after=5)
                    return

                try:
                    if len(d) == 1:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]]
                    elif len(d) == 2:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]]
                    elif len(d) == 3:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]]
                    elif len(d) == 4:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]]
                    elif len(d) == 5:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]]
                        
                except KeyError as e:
                    await ctx.send(f"That directory doesn't exist.\n`Invalid category: {e}`", delete_after=5)
                    return
                
                else:
                    try:
                        if len(d) == 1:
                            if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]], int):
                                raise KeyError(str(d[-1]))
                            else:
                                if name in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]].keys():
                                    await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                    return

                                category = await self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["categoryID"])
                                dchannel = await self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["channelID"])
                                channel = await category.create_text_channel(f"finishing-creation", topic=f"Go back: {dchannel.mention}; Name: \"{name}\"")
                                await channel.edit(name=str(f"{name}-{channel.id}"))
                        
                                self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]].update({name:channel.id})

                        elif len(d) == 2:
                            if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]], int):
                                raise KeyError(str(d[-1]))
                            else:
                                if name in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].keys():
                                    await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                    return

                                category = await self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["categoryID"])
                                dchannel = await self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["channelID"])
                                channel = await category.create_text_channel(f"finishing-creation", topic=f"Go back: {dchannel.mention}; Name: \"{name}\"")
                                await channel.edit(name=str(f"{name}-{channel.id}"))            
            
                                self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].update({name:channel.id})

                        elif len(d) == 3:
                            if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]], int):
                                raise KeyError(str(d[-1]))
                            else:
                                if name in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].keys():
                                    await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                    return

                                category = await self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["categoryID"])
                                dchannel = await self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["channelID"])
                                channel = await category.create_text_channel(f"finishing-creation", topic=f"Go back: {dchannel.mention}; Name: \"{name}\"")
                                await channel.edit(name=str(f"{name}-{channel.id}"))
                                
                                self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].update({name:channel.id})

                        elif len(d) == 4:
                            if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]], int):
                                raise KeyError(str(d[-1]))
                            else:
                                if name in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].keys():
                                    await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                    return

                                category = await self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["categoryID"])
                                dchannel = await self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["channelID"])
                                channel = await category.create_text_channel(f"finishing-creation", topic=f"Go back: {dchannel.mention}; Name: \"{name}\"")
                                await channel.edit(name=str(f"{name}-{channel.id}"))
                                
                                self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].update({name:channel.id})

                        elif len(d) == 5:
                            if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]], int):
                                raise KeyError(str(d[-1]))
                            else:
                                if name in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]].keys():
                                    await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                    return

                                category = await self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["categoryID"])
                                dchannel = await self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["channelID"])
                                channel = await category.create_text_channel(f"finishing-creation", topic=f"Go back: {dchannel.mention}; Name: \"{name}\"")
                                await channel.edit(name=str(f"{name}-{channel.id}"))
                                
                                self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]].update({name:channel.id})

                    except KeyError as e:
                        await ctx.send(f"Your last position, {e}, is a channel, not a category.\n`Invalid category: {e}`", delete_after=5)
                        return

                    else:
                        await self.update_directory(ctx, note=f"New channel; Name: {name}; Path: {directory}")
                        print(f"+ Added new channel to server \"{ctx.guild.name}\".")
            else:
                await ctx.send(f"This command must be used in the directory channel created by the bot.\nDeleted it? Use the command `{self.bot.cwd}update`.")
        else:
            await ctx.send(f"You don't have a directory yet. Use the `{self.bot.command_prefix}setup` command to create one.")
            return

     
    @commands.command(aliases=["new_cat"])
    @commands.bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True)
    async def create_category(self, ctx, directory, name):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in self.bot.univ.Directories.keys():
            if ctx.channel.id == self.bot.univ.Directories[ctx.guild.id]["channelID"]:
                await ctx.message.delete()
                if ctx.guild.id in self.bot.univ.LoadingUpdate.keys():
                    if self.bot.univ.LoadingUpdate[ctx.guild.id] == True:
                        await ctx.send("The directory is being updated at the moment. Try again in a few seconds.", delete_after=10)
                        return
                
                if len(name) > 50:
                    await ctx.send("\"name\" cannot be greater than 50.", delete_after=5)
                    return
                
                d = directory.split("//")
                
                try:
                    if len(d) == 1:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]]
                    elif len(d) == 2:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]]
                    elif len(d) == 3:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]]
                    elif len(d) == 4:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]]
                    elif len(d) == 5:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]]
                    else:
                        raise KeyError
                        
                except KeyError as e:
                    await ctx.send(f"That directory doesn't exist.\n`Invalid category name: \"{e}\"`", delete_after=5)

                else:
                    if len(d) == 1:
                        if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]], int):
                            raise KeyError(str(d[-1]))
                        else:
                            if name in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]].keys():
                                await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                return
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]].update({name:{}})

                    elif len(d) == 2:
                        if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]], int):
                            raise KeyError(str(d[-1]))
                        else:
                            if name in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].keys():
                                await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                return
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].update({name:{}})

                    elif len(d) == 3:
                        if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]], int):
                            raise KeyError(str(d[-1]))
                        else:
                            if name in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].keys():
                                await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                return
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].update({name:{}})

                    elif len(d) == 4:
                        if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]], int):
                            raise KeyError(str(d[-1]))
                        else:
                            if name in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].keys():
                                await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                return
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].update({name:{}})

                    elif len(d) == 5:
                        if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]], int):
                            raise KeyError(str(d[-1]))
                        else:
                            if name in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]].keys():
                                await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                return
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]].update({name:{}})

                    await self.update_directory(ctx, note=f"New category; Name: {name}; Path: {directory}")
                    print(f"+ Added new category to server \"{ctx.guild.name}\".")
            else:
                await ctx.send(f"This command must be used in the directory channel created by the bot.\nDeleted it? Use the command `{self.bot.command_prefix}update`.")
        else:
            await ctx.send(f"You don't have a directory yet. Use the `{self.bot.command_prefix}setup` command to create one.")

     
    @commands.command(aliases=["del_cat"])
    @commands.bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True)
    async def delete_category(self, ctx, directory, name):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in self.bot.univ.Directories.keys():
            if ctx.channel.id == self.bot.univ.Directories[ctx.guild.id]["channelID"]:
                await ctx.message.delete()
                if ctx.guild.id in self.bot.univ.LoadingUpdate.keys():
                    if self.bot.univ.LoadingUpdate[ctx.guild.id] == True:
                        await ctx.send("The directory is being updated at the moment. Try again in a few seconds.", delete_after=10)
                        return
                
                d = directory.split("//")
                try:
                    if len(d) == 1:
                        try:
                            if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][name], dict):
                                for ik, iv in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][name].items():
                                    if isinstance(iv, int):
                                        try:
                                            channel = await self.bot.fetch_channel(iv)
                                            await channel.delete()
                                        except NotFound:
                                            pass
                                        
                                    elif isinstance(iv, dict):
                                        for xk, xv in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][name][ik].items():
                                            if isinstance(xv, int):
                                                try:
                                                    channel = await self.bot.fetch_channel(xv)
                                                    await channel.delete()
                                                except NotFound:
                                                    pass
                                                
                                            elif isinstance(xv, dict):
                                                for yk, yv in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][name][ik][xk].items():
                                                    if isinstance(yv, int):
                                                        try:
                                                            channel = await self.bot.fetch_channel(yv)
                                                            await channel.delete()
                                                        except NotFound:
                                                            pass
                                                        
                                                    elif isinstance(yv, dict):
                                                        for zk, zv in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][name][ik][xk][yk].items():
                                                            if isinstance(zv, int):
                                                                try:
                                                                    channel = await self.bot.fetch_channel(zv)
                                                                    await channel.delete()
                                                                except NotFound:
                                                                    pass
                            else:
                                raise TypeError
                    
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]].pop(name)
                        except TypeError:
                            await ctx.send("That's a channel silly! If you need to, go to the channel and delete it yourself. I currently cannot do that myself.")

                    elif len(d) == 2:
                        try:
                            if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][name], dict):
                                for ik, iv in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][name].items():
                                    if isinstance(iv, int):
                                        try:
                                            channel = await self.bot.fetch_channel(iv)
                                            await channel.delete()
                                        except NotFound:
                                            pass
                                        
                                    elif isinstance(iv, dict):
                                        for xk, xv in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][name][ik].items():
                                            if isinstance(xv, int):
                                                try:
                                                    channel = await self.bot.fetch_channel(xv)
                                                    await channel.delete()
                                                except NotFound:
                                                    pass
                                                
                                            elif isinstance(xv, dict):
                                                for yk, yv in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][name][ik][xk].items():
                                                    if isinstance(yv, int):
                                                        try:
                                                            channel = await self.bot.fetch_channel(yv)
                                                            await channel.delete()
                                                        except NotFound:
                                                            pass
                                                        
                                                    elif isinstance(yv, dict):
                                                        for zk, yv in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][name][ik][xk][yk].items():
                                                            if isinstance(zv, int):
                                                                try:
                                                                    channel = await self.bot.fetch_channel(zv)
                                                                    await channel.delete()
                                                                except NotFound:
                                                                    pass
                            else:
                                raise TypeError
                                    
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].pop(name)
                        except TypeError:
                            await ctx.send("That's a channel silly! If you need to, go to the channel and delete it yourself. I currently cannot do that myself.")

                    elif len(d) == 3:
                        try:
                            if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][name], dict):
                                for ik, iv in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][name].items():
                                    if isinstance(iv, int):
                                        try:
                                            channel = await self.bot.fetch_channel(iv)
                                            await channel.delete()
                                        except NotFound:
                                            pass

                                    elif isinstance(iv, dict):
                                        for xk, xv in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][name][ik].items():
                                            if isinstance(xv, int):
                                                try:
                                                    channel = await self.bot.fetch_channel(xv)
                                                    await channel.delete()
                                                except NotFound:
                                                    pass
                                                
                                            elif isinstance(xv, dict):
                                                for yk, yv in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][name][ik][xk].items():
                                                    if isinstance(yv, int):
                                                        try:
                                                            channel = await self.bot.fetch_channel(yv)
                                                            await channel.delete()
                                                        except NotFound:
                                                            pass

                            else:
                                raise TypeError
                                
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].pop(name)
                        except TypeError:
                            await ctx.send("That's a channel silly! If you need to, go to the channel and delete it yourself. I currently cannot do that myself.")

                    elif len(d) == 4:
                        try:
                            if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][name], dict):
                                for ik, iv in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][name].items():
                                    if isinstance(iv, int):
                                        try:
                                            channel = await self.bot.fetch_channel(iv)
                                            await channel.delete()
                                        except NotFound:
                                            pass
                                        
                            else:
                                raise TypeError
                                    
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].pop(name)
                        except TypeError:
                            await ctx.send("That's a channel silly! If you need to, go to the channel and delete it yourself. I currently cannot do that myself.")

                    await self.update_directory(ctx, note=f"Deleted category; Name: {name}; Path: {directory}")
                    print(f"- Deleted category from server \"{ctx.guild.name}\".")

                except KeyError as e:
                    await ctx.send(f"That directory doesn't exist.\n`Invalid category name: \"{e}\"`", delete_after=5)
                    return
            else:
                await ctx.send(f"This command must be used in the directory channel created by the bot.\nDeleted it? Use the command `{self.bot.command_prefix}update`.")
        else:
            await ctx.send(f"You don't have a directory yet. Use the `{self.bot.command_prefix}setup` command to create one.")
            
     
    @commands.command(aliases=["rn_ch"])
    @commands.bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True)
    async def rename_channel(self, ctx, directory, name, rename):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in self.bot.univ.Directories.keys():
            if ctx.channel.id == self.bot.univ.Directories[ctx.guild.id]["channelID"]:
                await ctx.message.delete()
                if ctx.guild.id in self.bot.univ.LoadingUpdate.keys():
                    if self.bot.univ.LoadingUpdate[ctx.guild.id] == True:
                        await ctx.send("The directory is being updated at the moment. Try again in a few seconds.", delete_after=10)
                        return
                
                d = directory.split("//")
                
                if len(name) > 50:
                    await ctx.send("\"name\" cannot be greater than 50 characters long.", delete_after=5)
                    return
                
                try:
                    if len(d) == 1:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][rename] = self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]].pop(name)
                        if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][rename], int):
                            dchannel = self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["channelID"])
                            channel = self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][rename])
                            await channel.edit(topic=f"Go back: {dchannel.mention}; Name: \"{rename}\"")

                    elif len(d) == 2:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][rename] = self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].pop(name)
                        if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][rename], int):
                            dchannel = self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["channelID"])
                            channel = self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][rename])
                            await channel.edit(topic=f"Go back: {dchannel.mention}; Name: \"{rename}\"")
                                               
                    elif len(d) == 3:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][rename] = self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].pop(name)
                        if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][rename], int):
                            dchannel = self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["channelID"])
                            channel = self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][rename])
                            await channel.edit(topic=f"Go back: {dchannel.mention}; Name: \"{rename}\"")
                                               
                    elif len(d) == 4:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][rename] = self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].pop(name)
                        if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][rename], int):
                            dchannel = self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["channelID"])
                            channel = self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][rename])
                            await channel.edit(topic=f"Go back: {dchannel.mention}; Name: \"{rename}\"")
                                               
                    elif len(d) == 5:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]][rename] = self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]].pop(name)
                        if isinstance(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]][rename], int):
                            dchannel = self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["channelID"])
                            channel = self.bot.fetch_channel(self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][rename])
                            await channel.edit(topic=f"Go back: {dchannel.mention}; Name: \"{rename}\"")
    
                    else:
                        raise KeyError("You cannot go deeper than 5.")

                except KeyError as e:
                    await ctx.send(f"That directory doesn't exist.\n`Invalid category name: \"{e}\"`", delete_after=5)
                    return
                
                else:
                    await self.update_directory(ctx, note=f"Renamed channel `name` to `rename` in path `directory`.")
                    print(f"= Renamed a channel for server \"{ctx.guild.name}\".")
            else:
                await ctx.send(f"This command must be used in the directory channel created by the bot.\nDeleted it? Use the command `{self.bot.command_prefix}update`.")
        else:
            await ctx.send(f"You don't have a directory yet. Use the `{self.bot.command_prefix}setup` command to create one.")
            
     
    @commands.command(aliases=["mv_ch"])
    @commands.bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True)
    async def move_channel(self, ctx, directory, name, new_directory):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return

        if ctx.guild.id in self.bot.univ.Directories.keys():
            if ctx.channel.id == self.bot.univ.Directories[ctx.guild.id]["channelID"]:
                await ctx.message.delete()
                if ctx.guild.id in self.bot.univ.LoadingUpdate.keys():
                    if self.bot.univ.LoadingUpdate[ctx.guild.id] == True:
                        await ctx.send("The directory is being updated at the moment. Try again in a few seconds.", delete_after=10)
                        return
                
                d = directory.split("//")
                D = new_directory.split("//")
                
                if len(name) > 15:
                    await ctx.send("\"name\" cannot be greater than 15 characters long.", delete_after=5)
                    return

                try:
                    if len(d) == 1:
                        if name not in self.bot.univ.Directories[ctx.guild.id]["tree"][D[0]].keys():
                            Branch = self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]].pop(name)
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    elif len(d) == 2:
                        if name not in self.bot.univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]].keys():
                            Branch = self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].pop(name)
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    elif len(d) == 3:
                        if name not in self.bot.univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]][D[2]].keys():
                            Branch = self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].pop(name)
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    elif len(d) == 4:
                        if name not in self.bot.univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]][D[2]][D[3]].keys():
                            Branch = self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].pop(name)
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    elif len(d) == 5:
                        if name not in self.bot.univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]][D[2]][D[3]][D[4]].keys():
                            Branch = self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]].pop(name)
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    else:
                        raise KeyError("You cannot go deeper than 5.")

                except KeyError as e:
                    await ctx.send(f"That directory doesn't exist.\n`Invalid category name: \"{e}\"`", delete_after=5)
                    return

                try:
                    if len(D) == 1:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][D[0]][name] = Branch

                    elif len(D) == 2:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]][name] = Branch

                    elif len(D) == 3:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]][D[2]][name] = Branch

                    elif len(D) == 4:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]][D[2]][D[3]][name] = Branch

                    elif len(D) == 5:
                        self.bot.univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]][D[2]][D[3]][D[4]][name] = Branch

                    else:
                        raise KeyError("You cannot go deeper than 5.")

                except KeyError as e:
                    await ctx.send(f"That directory doesn't exist.\n`Invalid category name: \"{e}\"`", delete_after=5)
                    return
                
                else:
                    await self.update_directory(ctx, note=f"Moved channel `name` from path `directory` to `new_directory`.")
                    print(f"[] Moved a channel for server \"{ctx.guild.name}\".")
            else:
                await ctx.send(f"This command must be used in the directory channel created by the bot.\nDeleted it? Use the command `{self.bot.command_prefix}update`.")
        else:
            await ctx.send(f"You don't have a directory yet. Use the `{self.bot.command_prefix}setup` command to create one.")

     
    @commands.command(aliases=["imp_ch"])
    @commands.bot_has_permissions(send_messages=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True)
    async def import_channel(self, ctx, channel, new_directory, name):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in self.bot.univ.Directories.keys():
            if ctx.channel.id == self.bot.univ.Directories[ctx.guild.id]["channelID"]:
                await ctx.message.delete()
                if channel.startswith("<#") and channel.endswith(">"):
                    channel = channel.replace("<#", "")
                    channel = channel.replace(">", "")

                try:
                    channel = int(channel)
                except ValueError:
                    await ctx.send("Please mention the channel or provide its ID.", delete_after=5)
                    return

                d = new_directory.split("//")

                try:
                    if len(d) == 1:
                        if name not in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]].keys():
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][name] = channel
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    elif len(d) == 2:
                        if name not in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].keys():
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][name] = channel
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    elif len(d) == 3:
                        if name not in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].keys():
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][name] = channel
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    elif len(d) == 4:
                        if name not in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].keys():
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][name] = channel
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    elif len(d) == 5:
                        if name not in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]].keys():
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]][name] = channel
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    else:
                        raise KeyError("You cannot go deeper than 5.")

                except KeyError as e:
                    await ctx.send(f"That directory doesn't exist.\n`Invalid category name: \"{e}\"`", delete_after=5)
                    return

                await self.update_directory(ctx, note=f"Imported channel with name \"{name}\"; Path: \"{new_directory}\".")
            
            else:
                await ctx.send(f"This command must be used in the directory channel created by the bot.\nDeleted it? Use the command `{self.bot.command_prefix}update`.")
        else:
            await ctx.send(f"You don't have a directory yet. Use the `{self.bot.command_prefix}setup` command to create one.")

     
    @commands.command(aliases=["hd"])
    @commands.bot_has_permissions(send_messages=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True)
    async def hide_channel(self, ctx, directory, name):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in self.bot.univ.Directories.keys():
            if ctx.channel.id == self.bot.univ.Directories[ctx.guild.id]["channelID"]:
                await ctx.message.delete()

                d = directory.split("//")

                try:
                    if len(d) == 1:
                        if name in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]].keys():
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]].pop(name)
                        else:
                            await ctx.send("A channel with that name doesn't exist there.", delete_after=5)
                            return

                    elif len(d) == 2:
                        if name in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].keys():
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].pop(name)
                        else:
                            await ctx.send("A channel with that name doesn't exist there.", delete_after=5)
                            return

                    elif len(d) == 3:
                        if name in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].keys():
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].pop(name)
                        else:
                            await ctx.send("A channel with that name doesn't exist there.", delete_after=5)
                            return

                    elif len(d) == 4:
                        if name in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].keys():
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].pop(name)
                        else:
                            await ctx.send("A channel with that name doesn't exist there.", delete_after=5)
                            return

                    elif len(d) == 5:
                        if name in self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]].keys():
                            self.bot.univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]].pop(name)
                        else:
                            await ctx.send("A channel with that name doesn't exist there.", delete_after=5)
                            return

                    else:
                        raise KeyError("You cannot go deeper than 5.")

                except KeyError as e:
                    await ctx.send(f"That directory doesn't exist.\n`Invalid category name: \"{e}\"`", delete_after=5)
                    return

                await self.update_directory(ctx, note=f"Removed channel from directory, but was not deleted. Name: \"{name}\"; From Path: \"{directory}\".")
            
            else:
                await ctx.send(f"This command must be used in the directory channel created by the bot.\nDeleted it? Use the command `{BOT_PREFIX}update`.")
        else:
            await ctx.send(f"You don't have a directory yet. Use the `{self.bot.command_prefix}setup` command to create one.")

     
    @commands.command(aliases=["save"])
    @commands.bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True, attach_files=True)
    async def save_directory(self, ctx):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in self.bot.univ.Directories.keys():
            if ctx.channel.id == self.bot.univ.Directories[ctx.guild.id]["channelID"]:
                await ctx.send("You cannot use that command here.", delete_after=5)
            try:
                print("Creating file and closing...")
                open(f"{self.bot.cwd}\\Workspace\\cdr_directory.pkl", "x").close()
            except FileExistsError:
                pass

            with open(f"{self.bot.cwd}\\Workspace\\cdr_directory.pkl", "wb+") as f:
                data = await self.convert_to_readable(ctx)
                dump(data, f)
            
            with open(f"{self.bot.cwd}\\Workspace\\cdr_directory.pkl", "r") as f:
                file = File(f"{self.bot.cwd}\\Workspace\\cdr_directory.pkl")
                await ctx.send(f"This file contains pickled data using Python. Use the command `{self.bot.command_prefix}setup` and attach the file to load it.", file=file)

        else:
            await ctx.send(f"You don't have a directory yet. Use the `{self.bot.command_prefix}setup` command to create one.")
    
     
    @commands.command()
    @commands.bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True)
    async def update(self, ctx):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in self.bot.univ.Directories.keys():
            await ctx.message.delete()
            await self.update_directory(ctx, "Update requested manually.")
        else:
            await ctx.send(f"You don't have a directory yet. Use the `{self.bot.command_prefix}setup` command to create one.")

