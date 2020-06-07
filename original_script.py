# https://discord.com/oauth2/authorize?client_id=698965636432265227&permissions=268479504&scope=bot
global TimeZone
global debug_mode
debug_mode = input("Enter debug mode? (D=accept)\n---| ")
while True:
    TimeZone = input("Time Zone:\n---| ")
    if TimeZone in ["EST", "CST"]:
        break

print("Loading...")

import os
import sys
import copy
import asyncio
import pickle

from datetime import datetime

import dbl
import discord

from discord.ext import commands, tasks


Dir1 = os.getcwd()
print("Running in: "+Dir1)
print("Discord API version: " + discord.__version__)

# Main Initialize
#--------------------------------------------------------------
BOT_PREFIX = "cdr:"
BOT_TOKEN = '##'

bot = commands.Bot(
    command_prefix=BOT_PREFIX,
    description="Create new channel directory system in your servers.",
    owner_id=331551368789622784)

class Globals():
    def __init__(self):
        self.TearingDown = []

univ = Globals()

if not os.path.exists(f"{Dir1}\\Serialized\\data.pkl"):
    print("[Unable to save] data.pkl not found. Replace file before shutting down. Saving disabled.")
    univ.DisableSaving = True
    univ.Directories = {"guildID":{"catagoryID":0, "channelID":0, "msgID":0, "tree":{}}}

else:
    univ.DisableSaving = False
    with open(f"{Dir1}\\Serialized\\data.pkl", "rb") as f:
        try:
            univ.Directories = pickle.Unpickler(f).load()
            print("[] Loaded data.pkl.")
        except Exception as e:
            univ.Directories = {"guildID":{"catagoryID":0, "channelID":0, "msgID":0, "tree":{}}}
            print("[Data Reset] Unpickling Error:", e)

""" Note: Channel names as keys are the name that the user gave, so they may rename it.
{
        "root" : {
                "root-channelOne" : "ID",
                "root-channelTwo" : "ID",
                "level2" : {
                        "root-level2-channelOne" : "ID",
                        "root-level2-channelTwo" : "ID",
                        "level3" : {
                                "root-level2-level3-channelOne" : "ID",
                                "root-level2-level3-channelTwo" : "ID",
                                "level4" : {
                                        "root-level2-level3-level4-channelOne" : "ID",
                                        "root-level2-level3-level4-channelTwo" : "ID",
                                        "level5" : {
                                                "root-level2-level3-level4-level5-channelOne" : "ID",
                                                "root-level2-level3-level4-level5-channelTwo" : "ID",
                                        }   
                                }   
                        }
                }  
        }
}
"""

#--------------------------------------------------------------

# Tasks
#--------------------------------------------------------------

class Background_Tasks(commands.Cog):
    """Background loops"""
    def __init__(self, bot):
        self.bot = bot
        # self.DBLtoken = "token"
        # self.dblpy = dbl.DBLClient(self.bot, self.DBLtoken, autopost=True)
        self.savetofile.start()

    @tasks.loop(seconds=60)
    async def status_change(self):
        utchour = str(datetime.now().hour)
        utcminute = str(datetime.now().minute)
        if len(utchour) == 1:
            utchour = "0" + utchour
        if len(utcminute) == 1:
            utcminute = "0" + utcminute
        utctime = f"{utchour}:{utcminute}"

        if debug_mode == "D":
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="IN DEBUG MODE"))
        if univ.DisableSaving:
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"SAVING DISABLED"))
        else:
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{BOT_PREFIX}help | {TimeZone}: {utctime}"))
    
    @tasks.loop(seconds=60)
    async def savetofile(self):
        hour = str(datetime.now().hour)
        minute = str(datetime.now().minute)
        date = str(str(datetime.now().date().month) + "/" + str(datetime.now().date().day) + "/" + str(datetime.now().date().year))
        if len(hour) == 1:
            hour = "0" + hour
        if len(minute) == 1:
            minute = "0" + minute
        time = f"{hour}:{minute}, {date}"

        if not os.path.exists(f"{Dir1}\\Serialized\\data.pkl") and univ.DisableSaving == False:
            univ.DisableSaving = True
            print(f"[{time} || Unable to save] data.pkl not found. Replace file before shutting down. Saving disabled.")
            return

        elif os.path.exists(f"{Dir1}\\Serialized\\data.pkl") and univ.DisableSaving == True:
            univ.DisableSaving = False
            print(f"[{time}] Saving re-enabled.")
            return

        if univ.DisableSaving == False:
            with open(f"{Dir1}\\Serialized\\data.pkl", "wb") as f:
                try:
                    pickle.dump(univ.Directories, f)
                except Exception as e:
                    print(f"[{time} || Unable to save] Pickle dumping Error:", e)

            print(f"[CDR: {time}] Saved data.")

# Commands
#------------------------------------------------------------

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.LoadingUpdate = {"guildID":"bool"}

    bot.remove_command("help")

    async def convert_to_readable(self, ctx): # It is advised to use update_directory(ctx) first. 'ctx' must meet the requirements for getting .guild and its directory.
        directory = copy.deepcopy(univ.Directories[ctx.guild.id]["tree"])
        
        while True:
            if ctx.guild.id in self.LoadingUpdate:
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
        cat = await bot.fetch_channel(univ.Directories[ctx.guild.id]["categoryID"])
        dchannel = await bot.fetch_channel(univ.Directories[ctx.guild.id]["channelID"])

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
            dchannel = await bot.fetch_channel(univ.Directories[ctx.guild.id]["channelID"])	
        except discord.errors.NotFound:	
            try:	
                cat = await bot.fetch_channel(univ.Directories[ctx.guild.id]["categoryID"])	
            except discord.errors.NotFound:	
                await ctx.send("You need to set up your directory again.")	
                univ.Directories.pop(ctx.guild.id)
                return

            dchannel = await cat.create_text_channel("directory", topic="Managers: Leave this channel on top for easy access. Feel free to move or rename it.")	
            univ.Directories[ctx.guild.id]["channelID"] = dchannel.id
            msg = await dchannel.send("Completing repairs...")
            univ.Directories[ctx.guild.id]["msgID"] = msg.id
            
        try:	
            msg = await dchannel.fetch_message(univ.Directories[ctx.guild.id]["msgID"])	
        except discord.errors.NotFound:	
            msg = await dchannel.send("Completing repairs...")	
            univ.Directories[ctx.guild.id]["msgID"] = msg.id

        async with dchannel.typing():
            if list(univ.Directories[ctx.guild.id]["tree"]["root"].items()) == []:
                msg = await dchannel.fetch_message(univ.Directories[ctx.guild.id]["msgID"])
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
                    self.LoadingUpdate[ctx.guild.id] = True
                    for ik, iv in univ.Directories[ctx.guild.id]["tree"]["root"].items():
                        if isinstance(iv, int):
                            try:
                                channel = await bot.fetch_channel(iv)
                            except discord.NotFound:
                                univ.Directories[ctx.guild.id]["tree"]["root"].pop(ik)
                                return False
                            else:
                                message_lines.append(f"**ーー [** {ik} **>>>** ||{channel.mention}||")
                                
                        elif isinstance(iv, dict):
                            message_lines.append(f"**ーー Category: [** {ik} **]**")
                            for xk, xv in univ.Directories[ctx.guild.id]["tree"]["root"][ik].items():
                                if isinstance(xv, int):
                                    try:
                                        channel = await bot.fetch_channel(xv)
                                    except discord.NotFound:
                                        univ.Directories[ctx.guild.id]["tree"]["root"][ik].pop(xk)
                                        return False
                                    else:
                                        message_lines.append(f"**ーーーー [** {xk} **>>>** ||{channel.mention}||")

                                elif isinstance(xv, dict):
                                    message_lines.append(f"**ーーーー Category: [** {xk} **]**")
                                    for yk, yv in univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk].items():
                                        if isinstance(yv, int):
                                            try:
                                                channel = await bot.fetch_channel(yv)
                                            except discord.NotFound:
                                                univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk].pop(yk)
                                                return False
                                            else:
                                                message_lines.append(f"**ーーーーーー [** {yk} **>>>** ||{channel.mention}||")

                                        elif isinstance(yv, dict):
                                            message_lines.append(f"**ーーーーーー Category: [** {yk} **]**")
                                            for zk, zv in univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk][yk].items():
                                                if isinstance(zv, int):
                                                    try:
                                                        channel = await bot.fetch_channel(zv)
                                                    except discord.NotFound:
                                                        univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk][yk].pop(zk)
                                                        return False
                                                    else:
                                                        message_lines.append(f"**ーーーーーーーー [** {zk} **>>>** ||{channel.mention}||")

                                                elif isinstance(zv, dict):
                                                    message_lines.append(f"**ーーーーーーーー Category: [** {zk} **]**")
                                                    for ak, av in univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk][yk][zk].items():
                                                        if isinstance(av, int):
                                                            try:
                                                                channel = await bot.fetch_channel(av)
                                                            except discord.NotFound:
                                                                univ.Directories[ctx.guild.id]["tree"]["root"][ik][xk][yk][zk].pop(ak)
                                                                return False
                                                            else:
                                                                message_lines.append(f"**ーーーーーーーーーー [** {ak} **>>>** ||{channel.mention}||")
                    
                    return True

                while True:
                    dchannel = await bot.fetch_channel(univ.Directories[ctx.guild.id]["channelID"])
                    msg = await dchannel.fetch_message(univ.Directories[ctx.guild.id]["msgID"])
                    result = await read()
                    if result is False:
                        message_lines = []
                        continue
                    else:

                        self.LoadingUpdate[ctx.guild.id] = False
                        if list(univ.Directories[ctx.guild.id]["tree"]["root"].items()) == []:
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
                                message = await dchannel.fetch_message(univ.Directories[ctx.guild.id]["msgID"])
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

    @commands.command(name="setup", aliases=["su"])
    @commands.bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True, manage_roles=True)
    @commands.has_permissions(manage_channels=True, manage_guild=True)
    async def setup_directory(self, ctx):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in univ.Directories.keys():
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
            reaction, user = await bot.wait_for("reaction_add", timeout=30, check=check)
        except asyncio.TimeoutError:
            await msg.delete()
        else:
            await reaction.remove(user)
            if ctx.guild.id in univ.Directories.keys():
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
            await asyncio.sleep(2)
            if ctx.guild.id in univ.Directories.keys():
                await msg.edit(content="Note: Your old channels will not be deleted, but the old directory channel will not be kept updated or managed anymore.")
                univ.Directories.pop(ctx.guild.id)
                await asyncio.sleep(5)

            if ctx.guild.id not in univ.Directories.keys():
                if ctx.message.attachments != []:
                    file = None
                    for i in ctx.message.attachments:
                        if i.filename == f"cdr_directory.pkl":
                            file = i
                            break

                    await msg.edit(content="You've attached a valid file to your message. Do you want to attempt to load it?\nReact with :white_check_mark: (within 10 seconds) to continue the setup.\n`[  ]`")
                    def check(reaction, user):
                        return str(reaction.emoji) == "✅" and user == ctx.author and reaction.message.id == msg.id
                    
                    try:
                        reaction, user = await bot.wait_for("reaction_add", timeout=10, check=check)
                    except asyncio.TimeoutError:
                        await msg.delete()
                        return
                    else:
                        await reaction.remove(user)
                        await msg.edit(content="You've attached a valid file to your message. Do you want to attempt to load it?\nReact with :white_check_mark: (within 10 seconds) to continue the setup.\n`[✅]`")
                        await asyncio.sleep(2)

                        self.LoadingUpdate.update({ctx.guild.id:True})
                        await msg.edit(content="Setting up with attached file...")

                        file = await file.save(f"{Dir1}\\Workspace\\incoming.pkl")
                        with open(f"{Dir1}\\Workspace\\incoming.pkl", "rb") as f:
                            tree = pickle.Unpickler(f).load()

                        os.remove(f"{Dir1}\\Workspace\\incoming.pkl")

                        cat = await ctx.guild.create_category("CDR: Directories (Bot Managed)")
                        directory = await cat.create_text_channel("directory", topic="Managers: Leave this channel on top for easy access. Also do not delete it.")
                        
                        await directory.set_permissions(ctx.guild.default_role, send_messages=False)
                        member_self = await ctx.guild.fetch_member(bot.user.id)
                        await directory.set_permissions(member_self, send_messages=True)

                        dmessage = await directory.send("Adding channels...")

                        univ.Directories.update({ctx.guild.id:{"categoryID":cat.id, "channelID":directory.id, "msgID":dmessage.id, "tree":tree}})

                        try:
                            tree = await self.convert_to_directory(ctx, tree)
                        except TypeError:
                            await msg.edit(content="The setup failed because the file is either changed, corrupted, or outdated.")
                            return
                        else:
                            await self.update_directory(ctx, note="Finished automated setup.")
                            await msg.edit(content=f"Finished setup. Get to the directory here: {directory.mention}")

                        self.LoadingUpdate.update({ctx.guild.id:False})
                else:
                    await msg.edit(content="Setting up now...")
                    cat = await ctx.guild.create_category("CDR: Directories (Bot Managed)")
                    directory = await cat.create_text_channel("directory", topic="Managers: Leave this channel on top for easy access. Also do not delete it.")
                    
                    await directory.set_permissions(ctx.guild.default_role, send_messages=False)
                    member_self = await ctx.guild.fetch_member(bot.user.id)
                    await directory.set_permissions(member_self, send_messages=True)

                    dmessage = await directory.send("This channel will have a directory under it when you create a channel using the special command that I provide to you.\nAlso, make sure I have access to all channels added.\nYou are free to move this channel, but it's best to leave on top.")
                    await msg.edit(content=f"Finished setup. Get to the directory here: {directory.mention}")

                    univ.Directories.update({ctx.guild.id:{"categoryID":cat.id, "channelID":directory.id, "msgID":dmessage.id, "tree":{"root":{}}}})
                
    #--------------------------------------------------------------------------------------------------------------------------
    @commands.command(name="teardown", aliases=["td"])
    @commands.bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True, manage_guild=True)
    async def teardown_directory(self, ctx, categoryID: int = 0):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return

        if categoryID == 0:    
            if ctx.guild.id in univ.Directories.keys():
                if ctx.channel.id == univ.Directories[ctx.guild.id]["channelID"]:
                    await ctx.send("You can't do that here!", delete_after=5)
                    return

                msg = await ctx.send("Are you sure? React with :white_check_mark: (within 20 seconds) to continue.\nIf you want to, you can save your directory first using the `save_directory` command.\n`[  ]`")
                def check(reaction, user):
                    return str(reaction.emoji) == "✅" and user == ctx.author and reaction.message.id == msg.id
                
                try:
                    reaction, user = await bot.wait_for("reaction_add", timeout=10, check=check)
                except asyncio.TimeoutError:
                    await msg.delete()
                else:
                    await reaction.remove(user)
                    await msg.edit(content="Are you sure? React with :white_check_mark: (within 20 seconds) to continue.\nIf you want to, you can save your directory first using the `save_directory` command.\n`[✅]`")
                    await asyncio.sleep(2)
                    await msg.edit(content="Tearing down...")
                    univ.TearingDown.append(ctx.guild.id)
                    try:
                        category = await bot.fetch_channel(univ.Directories[ctx.guild.id]["categoryID"])
                    except discord.errors.NotFound:
                        await msg.edit(content="I couldn't find the category for the channels.")
                        univ.Directories.pop(ctx.guild.id)
                        univ.TearingDown.remove(ctx.guild.id)
                        return

                    for i in category.channels:
                        await i.delete()

                    await category.delete()

                    univ.Directories.pop(ctx.guild.id)
                    univ.TearingDown.remove(ctx.guild.id)
                    await msg.edit(content="Teardown complete.")
            else:
                await ctx.send("You don't have a directory to tear down.")
        else:
            if ctx.guild.id in univ.Directories.keys() and ctx.channel.id == univ.Directories[ctx.guild.id]["channelID"]:
                await ctx.send("You can't do that here!", delete_after=5)
                return
            
            if ctx.guild.id in univ.Directories.keys() and categoryID == univ.Directories[ctx.guild.id]["categoryID"]:
                await ctx.send("You cannot specify the external category used for the directory. In that case, don't specify any ID.", delete_after=5)
                return

            try:
                category = await bot.fetch_channel(categoryID)
            except discord.errors.NotFound:
                await ctx.send("No category with that ID exists.")
            else:
                if not categoryID in [guild.id for guild in ctx.guild.channels]:
                    await ctx.send("That category does exist, but it isn't in your server. Why would I let you do that? Spoiled prankster.")
                    return
    
            msg = await ctx.send("Are you sure? React with :white_check_mark: (within 20 seconds) to continue.\nConfirm: You are deleting an external category.\n`[  ]`")
            def check(reaction, user):
                return str(reaction.emoji) == "✅" and user == ctx.author and reaction.message.id == msg.id
            
            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=10, check=check)
            except asyncio.TimeoutError:
                await msg.delete()
            else:
                await reaction.remove(user)
                await msg.edit(content="Are you sure? React with :white_check_mark: (within 20 seconds) to continue.\nConfirm: You are deleting an external category.\n`[✅]`")
                await asyncio.sleep(2)
                await msg.edit(content="Tearing down external category...")
                univ.TearingDown.append(ctx.guild.id)
                
                for i in category.channels:
                    await i.delete()

                await category.delete()

                univ.TearingDown.remove(ctx.guild.id)
                await msg.edit(content="Teardown complete. Note that imported channels from that directory will no longer appear in the directory if you have it set up.")
                if ctx.guild.id in univ.Directories.keys():
                    await self.update_directory(ctx, note="External category deletion; Imported channels from that category now removed.")

    #--------------------------------------------------------------------------------------------------------------------------
    @commands.command(aliases=["new_ch"])
    @commands.bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True)
    async def create_channel(self, ctx, directory, name):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in univ.Directories.keys():
            if ctx.channel.id == univ.Directories[ctx.guild.id]["channelID"]:
                await ctx.message.delete()
                if ctx.guild.id in self.LoadingUpdate.keys():
                    if self.LoadingUpdate[ctx.guild.id] == True:
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
                        univ.Directories[ctx.guild.id]["tree"][d[0]]
                    elif len(d) == 2:
                        univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]]
                    elif len(d) == 3:
                        univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]]
                    elif len(d) == 4:
                        univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]]
                    elif len(d) == 5:
                        univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]]
                        
                except KeyError as e:
                    await ctx.send(f"That directory doesn't exist.\n`Invalid category: {e}`", delete_after=5)
                    return
                
                else:
                    try:
                        if len(d) == 1:
                            if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]], int):
                                raise KeyError(str(d[-1]))
                            else:
                                if name in univ.Directories[ctx.guild.id]["tree"][d[0]].keys():
                                    await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                    return

                                category = await bot.fetch_channel(univ.Directories[ctx.guild.id]["categoryID"])
                                dchannel = await bot.fetch_channel(univ.Directories[ctx.guild.id]["channelID"])
                                channel = await category.create_text_channel(f"finishing-creation", topic=f"Go back: {dchannel.mention}; Name: \"{name}\"")
                                await channel.edit(name=str(f"{name}-{channel.id}"))
                        
                                univ.Directories[ctx.guild.id]["tree"][d[0]].update({name:channel.id})

                        elif len(d) == 2:
                            if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]], int):
                                raise KeyError(str(d[-1]))
                            else:
                                if name in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].keys():
                                    await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                    return

                                category = await bot.fetch_channel(univ.Directories[ctx.guild.id]["categoryID"])
                                dchannel = await bot.fetch_channel(univ.Directories[ctx.guild.id]["channelID"])
                                channel = await category.create_text_channel(f"finishing-creation", topic=f"Go back: {dchannel.mention}; Name: \"{name}\"")
                                await channel.edit(name=str(f"{name}-{channel.id}"))            
            
                                univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].update({name:channel.id})

                        elif len(d) == 3:
                            if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]], int):
                                raise KeyError(str(d[-1]))
                            else:
                                if name in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].keys():
                                    await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                    return

                                category = await bot.fetch_channel(univ.Directories[ctx.guild.id]["categoryID"])
                                dchannel = await bot.fetch_channel(univ.Directories[ctx.guild.id]["channelID"])
                                channel = await category.create_text_channel(f"finishing-creation", topic=f"Go back: {dchannel.mention}; Name: \"{name}\"")
                                await channel.edit(name=str(f"{name}-{channel.id}"))
                                
                                univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].update({name:channel.id})

                        elif len(d) == 4:
                            if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]], int):
                                raise KeyError(str(d[-1]))
                            else:
                                if name in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].keys():
                                    await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                    return

                                category = await bot.fetch_channel(univ.Directories[ctx.guild.id]["categoryID"])
                                dchannel = await bot.fetch_channel(univ.Directories[ctx.guild.id]["channelID"])
                                channel = await category.create_text_channel(f"finishing-creation", topic=f"Go back: {dchannel.mention}; Name: \"{name}\"")
                                await channel.edit(name=str(f"{name}-{channel.id}"))
                                
                                univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].update({name:channel.id})

                        elif len(d) == 5:
                            if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]], int):
                                raise KeyError(str(d[-1]))
                            else:
                                if name in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]].keys():
                                    await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                    return

                                category = await bot.fetch_channel(univ.Directories[ctx.guild.id]["categoryID"])
                                dchannel = await bot.fetch_channel(univ.Directories[ctx.guild.id]["channelID"])
                                channel = await category.create_text_channel(f"finishing-creation", topic=f"Go back: {dchannel.mention}; Name: \"{name}\"")
                                await channel.edit(name=str(f"{name}-{channel.id}"))
                                
                                univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]].update({name:channel.id})

                    except KeyError as e:
                        await ctx.send(f"Your last position, {e}, is a channel, not a category.\n`Invalid category: {e}`", delete_after=5)
                        return

                    else:
                        await self.update_directory(ctx, note=f"New channel; Name: {name}; Path: {directory}")
                        print(f"+ Added new channel to server \"{ctx.guild.name}\".")
            else:
                await ctx.send(f"This command must be used in the directory channel created by the bot.\nDeleted it? Use the command `{BOT_PREFIX}update`.")
        else:
            await ctx.send(f"You don't have a directory yet. Use the `{BOT_PREFIX}setup` command to create one.")
            return

    #--------------------------------------------------------------------------------------------------------------------------
    @commands.command(aliases=["new_cat"])
    @commands.bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True)
    async def create_category(self, ctx, directory, name):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in univ.Directories.keys():
            if ctx.channel.id == univ.Directories[ctx.guild.id]["channelID"]:
                await ctx.message.delete()
                if ctx.guild.id in self.LoadingUpdate.keys():
                    if self.LoadingUpdate[ctx.guild.id] == True:
                        await ctx.send("The directory is being updated at the moment. Try again in a few seconds.", delete_after=10)
                        return
                
                if len(name) > 50:
                    await ctx.send("\"name\" cannot be greater than 50.", delete_after=5)
                    return
                
                d = directory.split("//")
                
                try:
                    if len(d) == 1:
                        univ.Directories[ctx.guild.id]["tree"][d[0]]
                    elif len(d) == 2:
                        univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]]
                    elif len(d) == 3:
                        univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]]
                    elif len(d) == 4:
                        univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]]
                    elif len(d) == 5:
                        univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]]
                    else:
                        raise KeyError
                        
                except KeyError as e:
                    await ctx.send(f"That directory doesn't exist.\n`Invalid category name: \"{e}\"`", delete_after=5)

                else:
                    if len(d) == 1:
                        if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]], int):
                            raise KeyError(str(d[-1]))
                        else:
                            if name in univ.Directories[ctx.guild.id]["tree"][d[0]].keys():
                                await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                return
                            univ.Directories[ctx.guild.id]["tree"][d[0]].update({name:{}})

                    elif len(d) == 2:
                        if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]], int):
                            raise KeyError(str(d[-1]))
                        else:
                            if name in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].keys():
                                await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                return
                            univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].update({name:{}})

                    elif len(d) == 3:
                        if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]], int):
                            raise KeyError(str(d[-1]))
                        else:
                            if name in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].keys():
                                await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                return
                            univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].update({name:{}})

                    elif len(d) == 4:
                        if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]], int):
                            raise KeyError(str(d[-1]))
                        else:
                            if name in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].keys():
                                await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                return
                            univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].update({name:{}})

                    elif len(d) == 5:
                        if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]], int):
                            raise KeyError(str(d[-1]))
                        else:
                            if name in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]].keys():
                                await ctx.send("A channel or category in that directory already exists.", delete_after=5)
                                return
                            univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]].update({name:{}})

                    await self.update_directory(ctx, note=f"New category; Name: {name}; Path: {directory}")
                    print(f"+ Added new category to server \"{ctx.guild.name}\".")
            else:
                await ctx.send(f"This command must be used in the directory channel created by the bot.\nDeleted it? Use the command `{BOT_PREFIX}update`.")
        else:
            await ctx.send(f"You don't have a directory yet. Use the `{BOT_PREFIX}setup` command to create one.")

    #--------------------------------------------------------------------------------------------------------------------------
    @commands.command(aliases=["del_cat"])
    @commands.bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True)
    async def delete_category(self, ctx, directory, name):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in univ.Directories.keys():
            if ctx.channel.id == univ.Directories[ctx.guild.id]["channelID"]:
                await ctx.message.delete()
                if ctx.guild.id in self.LoadingUpdate.keys():
                    if self.LoadingUpdate[ctx.guild.id] == True:
                        await ctx.send("The directory is being updated at the moment. Try again in a few seconds.", delete_after=10)
                        return
                
                d = directory.split("//")
                try:
                    if len(d) == 1:
                        try:
                            if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]][name], dict):
                                for ik, iv in univ.Directories[ctx.guild.id]["tree"][d[0]][name].items():
                                    if isinstance(iv, int):
                                        try:
                                            channel = await bot.fetch_channel(iv)
                                            await channel.delete()
                                        except discord.NotFound:
                                            pass
                                        
                                    elif isinstance(iv, dict):
                                        for xk, xv in univ.Directories[ctx.guild.id]["tree"][d[0]][name][ik].items():
                                            if isinstance(xv, int):
                                                try:
                                                    channel = await bot.fetch_channel(xv)
                                                    await channel.delete()
                                                except discord.NotFound:
                                                    pass
                                                
                                            elif isinstance(xv, dict):
                                                for yk, yv in univ.Directories[ctx.guild.id]["tree"][d[0]][name][ik][xk].items():
                                                    if isinstance(yv, int):
                                                        try:
                                                            channel = await bot.fetch_channel(yv)
                                                            await channel.delete()
                                                        except discord.NotFound:
                                                            pass
                                                        
                                                    elif isinstance(yv, dict):
                                                        for zk, zv in univ.Directories[ctx.guild.id]["tree"][d[0]][name][ik][xk][yk].items():
                                                            if isinstance(zv, int):
                                                                try:
                                                                    channel = await bot.fetch_channel(zv)
                                                                    await channel.delete()
                                                                except discord.NotFound:
                                                                    pass
                            else:
                                raise TypeError
                    
                            univ.Directories[ctx.guild.id]["tree"][d[0]].pop(name)
                        except TypeError:
                            await ctx.send("That's a channel silly! If you need to, go to the channel and delete it yourself. I currently cannot do that myself.")

                    elif len(d) == 2:
                        try:
                            if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][name], dict):
                                for ik, iv in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][name].items():
                                    if isinstance(iv, int):
                                        try:
                                            channel = await bot.fetch_channel(iv)
                                            await channel.delete()
                                        except discord.NotFound:
                                            pass
                                        
                                    elif isinstance(iv, dict):
                                        for xk, xv in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][name][ik].items():
                                            if isinstance(xv, int):
                                                try:
                                                    channel = await bot.fetch_channel(xv)
                                                    await channel.delete()
                                                except discord.NotFound:
                                                    pass
                                                
                                            elif isinstance(xv, dict):
                                                for yk, yv in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][name][ik][xk].items():
                                                    if isinstance(yv, int):
                                                        try:
                                                            channel = await bot.fetch_channel(yv)
                                                            await channel.delete()
                                                        except discord.errors.NotFound:
                                                            pass
                                                        
                                                    elif isinstance(yv, dict):
                                                        for zk, yv in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][name][ik][xk][yk].items():
                                                            if isinstance(zv, int):
                                                                try:
                                                                    channel = await bot.fetch_channel(zv)
                                                                    await channel.delete()
                                                                except discord.NotFound:
                                                                    pass
                            else:
                                raise TypeError
                                    
                            univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].pop(name)
                        except TypeError:
                            await ctx.send("That's a channel silly! If you need to, go to the channel and delete it yourself. I currently cannot do that myself.")

                    elif len(d) == 3:
                        try:
                            if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][name], dict):
                                for ik, iv in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][name].items():
                                    if isinstance(iv, int):
                                        try:
                                            channel = await bot.fetch_channel(iv)
                                            await channel.delete()
                                        except discord.NotFound:
                                            pass

                                    elif isinstance(iv, dict):
                                        for xk, xv in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][name][ik].items():
                                            if isinstance(xv, int):
                                                try:
                                                    channel = await bot.fetch_channel(xv)
                                                    await channel.delete()
                                                except discord.NotFound:
                                                    pass
                                                
                                            elif isinstance(xv, dict):
                                                for yk, yv in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][name][ik][xk].items():
                                                    if isinstance(yv, int):
                                                        try:
                                                            channel = await bot.fetch_channel(yv)
                                                            await channel.delete()
                                                        except discord.NotFound:
                                                            pass

                            else:
                                raise TypeError
                                
                            univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].pop(name)
                        except TypeError:
                            await ctx.send("That's a channel silly! If you need to, go to the channel and delete it yourself. I currently cannot do that myself.")

                    elif len(d) == 4:
                        try:
                            if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][name], dict):
                                for ik, iv in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][name].items():
                                    if isinstance(iv, int):
                                        try:
                                            channel = await bot.fetch_channel(iv)
                                            await channel.delete()
                                        except discord.NotFound:
                                            pass
                                        
                            else:
                                raise TypeError
                                    
                            univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].pop(name)
                        except TypeError:
                            await ctx.send("That's a channel silly! If you need to, go to the channel and delete it yourself. I currently cannot do that myself.")

                    await self.update_directory(ctx, note=f"Deleted category; Name: {name}; Path: {directory}")
                    print(f"- Deleted category from server \"{ctx.guild.name}\".")

                except KeyError as e:
                    await ctx.send(f"That directory doesn't exist.\n`Invalid category name: \"{e}\"`", delete_after=5)
                    return
            else:
                await ctx.send(f"This command must be used in the directory channel created by the bot.\nDeleted it? Use the command `{BOT_PREFIX}update`.")
        else:
            await ctx.send(f"You don't have a directory yet. Use the `{BOT_PREFIX}setup` command to create one.")
            
    #--------------------------------------------------------------------------------------------------------------------------
    @commands.command(aliases=["rn_ch"])
    @commands.bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True)
    async def rename_channel(self, ctx, directory, name, rename):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in univ.Directories.keys():
            if ctx.channel.id == univ.Directories[ctx.guild.id]["channelID"]:
                await ctx.message.delete()
                if ctx.guild.id in self.LoadingUpdate.keys():
                    if self.LoadingUpdate[ctx.guild.id] == True:
                        await ctx.send("The directory is being updated at the moment. Try again in a few seconds.", delete_after=10)
                        return
                
                d = directory.split("//")
                
                if len(name) > 50:
                    await ctx.send("\"name\" cannot be greater than 50 characters long.", delete_after=5)
                    return
                
                try:
                    if len(d) == 1:
                        univ.Directories[ctx.guild.id]["tree"][d[0]][rename] = univ.Directories[ctx.guild.id]["tree"][d[0]].pop(name)
                        if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]][rename], int):
                            dchannel = bot.fetch_channel(univ.Directories[ctx.guild.id]["channelID"])
                            channel = bot.fetch_channel(univ.Directories[ctx.guild.id]["tree"][d[0]][rename])
                            await channel.edit(topic=f"Go back: {dchannel.mention}; Name: \"{rename}\"")

                    elif len(d) == 2:
                        univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][rename] = univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].pop(name)
                        if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][rename], int):
                            dchannel = bot.fetch_channel(univ.Directories[ctx.guild.id]["channelID"])
                            channel = bot.fetch_channel(univ.Directories[ctx.guild.id]["tree"][d[0]][rename])
                            await channel.edit(topic=f"Go back: {dchannel.mention}; Name: \"{rename}\"")
                                               
                    elif len(d) == 3:
                        univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][rename] = univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].pop(name)
                        if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][rename], int):
                            dchannel = bot.fetch_channel(univ.Directories[ctx.guild.id]["channelID"])
                            channel = bot.fetch_channel(univ.Directories[ctx.guild.id]["tree"][d[0]][rename])
                            await channel.edit(topic=f"Go back: {dchannel.mention}; Name: \"{rename}\"")
                                               
                    elif len(d) == 4:
                        univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][rename] = univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].pop(name)
                        if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][rename], int):
                            dchannel = bot.fetch_channel(univ.Directories[ctx.guild.id]["channelID"])
                            channel = bot.fetch_channel(univ.Directories[ctx.guild.id]["tree"][d[0]][rename])
                            await channel.edit(topic=f"Go back: {dchannel.mention}; Name: \"{rename}\"")
                                               
                    elif len(d) == 5:
                        univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]][rename] = univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]].pop(name)
                        if isinstance(univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]][rename], int):
                            dchannel = bot.fetch_channel(univ.Directories[ctx.guild.id]["channelID"])
                            channel = bot.fetch_channel(univ.Directories[ctx.guild.id]["tree"][d[0]][rename])
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
                await ctx.send(f"This command must be used in the directory channel created by the bot.\nDeleted it? Use the command `{BOT_PREFIX}update`.")
        else:
            await ctx.send(f"You don't have a directory yet. Use the `{BOT_PREFIX}setup` command to create one.")
            
    #--------------------------------------------------------------------------------------------------------------------------
    @commands.command(aliases=["mv_ch"])
    @commands.bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True)
    async def move_channel(self, ctx, directory, name, new_directory):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in univ.Directories.keys():
            if ctx.channel.id == univ.Directories[ctx.guild.id]["channelID"]:
                await ctx.message.delete()
                if ctx.guild.id in self.LoadingUpdate.keys():
                    if self.LoadingUpdate[ctx.guild.id] == True:
                        await ctx.send("The directory is being updated at the moment. Try again in a few seconds.", delete_after=10)
                        return
                
                d = directory.split("//")
                D = new_directory.split("//")
                
                if len(name) > 15:
                    await ctx.send("\"name\" cannot be greater than 15 characters long.", delete_after=5)
                    return

                try:
                    if len(d) == 1:
                        if name not in univ.Directories[ctx.guild.id]["tree"][D[0]].keys():
                            Branch = univ.Directories[ctx.guild.id]["tree"][d[0]].pop(name)
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    elif len(d) == 2:
                        if name not in univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]].keys():
                            Branch = univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].pop(name)
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    elif len(d) == 3:
                        if name not in univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]][D[2]].keys():
                            Branch = univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].pop(name)
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    elif len(d) == 4:
                        if name not in univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]][D[2]][D[3]].keys():
                            Branch = univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].pop(name)
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    elif len(d) == 5:
                        if name not in univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]][D[2]][D[3]][D[4]].keys():
                            Branch = univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]].pop(name)
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
                        univ.Directories[ctx.guild.id]["tree"][D[0]][name] = Branch

                    elif len(D) == 2:
                        univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]][name] = Branch

                    elif len(D) == 3:
                        univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]][D[2]][name] = Branch

                    elif len(D) == 4:
                        univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]][D[2]][D[3]][name] = Branch

                    elif len(D) == 5:
                        univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]][D[2]][D[3]][D[4]][name] = Branch

                    else:
                        raise KeyError("You cannot go deeper than 5.")

                except KeyError as e:
                    await ctx.send(f"That directory doesn't exist.\n`Invalid category name: \"{e}\"`", delete_after=5)
                    return
                
                else:
                    await self.update_directory(ctx, note=f"Moved channel `name` from path `directory` to `new_directory`.")
                    print(f"[] Moved a channel for server \"{ctx.guild.name}\".")
            else:
                await ctx.send(f"This command must be used in the directory channel created by the bot.\nDeleted it? Use the command `{BOT_PREFIX}update`.")
        else:
            await ctx.send(f"You don't have a directory yet. Use the `{BOT_PREFIX}setup` command to create one.")

    #--------------------------------------------------------------------------------------------------------------------------
    @commands.command(aliases=["imp_ch"])
    @commands.bot_has_permissions(send_messages=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True)
    async def import_channel(self, ctx, channel, new_directory, name):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in univ.Directories.keys():
            if ctx.channel.id == univ.Directories[ctx.guild.id]["channelID"]:
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
                        if name not in univ.Directories[ctx.guild.id]["tree"][d[0]].keys():
                            univ.Directories[ctx.guild.id]["tree"][d[0]][name] = channel
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    elif len(d) == 2:
                        if name not in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].keys():
                            univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][name] = channel
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    elif len(d) == 3:
                        if name not in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].keys():
                            univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][name] = channel
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    elif len(d) == 4:
                        if name not in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].keys():
                            univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][name] = channel
                        else:
                            await ctx.send("The destination directory already has a channel or category with the same name.", delete_after=5)
                            return

                    elif len(d) == 5:
                        if name not in univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]][D[2]][D[3]][D[4]].keys():
                            univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]][name] = channel
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
                await ctx.send(f"This command must be used in the directory channel created by the bot.\nDeleted it? Use the command `{BOT_PREFIX}update`.")
        else:
            await ctx.send(f"You don't have a directory yet. Use the `{BOT_PREFIX}setup` command to create one.")

    #--------------------------------------------------------------------------------------------------------------------------
    @commands.command(aliases=["hd"])
    @commands.bot_has_permissions(send_messages=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True)
    async def hide_channel(self, ctx, directory, name):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in univ.Directories.keys():
            if ctx.channel.id == univ.Directories[ctx.guild.id]["channelID"]:
                await ctx.message.delete()

                d = directory.split("//")

                try:
                    if len(d) == 1:
                        if name in univ.Directories[ctx.guild.id]["tree"][d[0]].keys():
                            univ.Directories[ctx.guild.id]["tree"][d[0]].pop(name)
                        else:
                            await ctx.send("A channel with that name doesn't exist there.", delete_after=5)
                            return

                    elif len(d) == 2:
                        if name in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].keys():
                            univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]].pop(name)
                        else:
                            await ctx.send("A channel with that name doesn't exist there.", delete_after=5)
                            return

                    elif len(d) == 3:
                        if name in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].keys():
                            univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]].pop(name)
                        else:
                            await ctx.send("A channel with that name doesn't exist there.", delete_after=5)
                            return

                    elif len(d) == 4:
                        if name in univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].keys():
                            univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]].pop(name)
                        else:
                            await ctx.send("A channel with that name doesn't exist there.", delete_after=5)
                            return

                    elif len(d) == 5:
                        if name in univ.Directories[ctx.guild.id]["tree"][D[0]][D[1]][D[2]][D[3]][D[4]].keys():
                            univ.Directories[ctx.guild.id]["tree"][d[0]][d[1]][d[2]][d[3]][d[4]].pop(name)
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
            await ctx.send(f"You don't have a directory yet. Use the `{BOT_PREFIX}setup` command to create one.")

    #--------------------------------------------------------------------------------------------------------------------------
    @commands.command(aliases=["save"])
    @commands.bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True, attach_files=True)
    async def save_directory(self, ctx):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in univ.Directories.keys():
            if ctx.channel.id == univ.Directories[ctx.guild.id]["channelID"]:
                await ctx.send("You cannot use that command here.", delete_after=5)
            try:
                print("Creating file and closing...")
                open(f"{Dir1}\\Workspace\\cdr_directory.pkl", "x").close()
            except FileExistsError:
                pass

            with open(f"{Dir1}\\Workspace\\cdr_directory.pkl", "wb+") as f:
                data = await self.convert_to_readable(ctx)
                pickle.dump(data, f)
            
            with open(f"{Dir1}\\Workspace\\cdr_directory.pkl", "r") as f:
                file = discord.File(f"{Dir1}\\Workspace\\cdr_directory.pkl")
                await ctx.send(f"This file contains pickled data using Python. Use the command `{BOT_PREFIX}setup` and attach the file to load it.", file=file)

        else:
            await ctx.send(f"You don't have a directory yet. Use the `{BOT_PREFIX}setup` command to create one.")
    
    #--------------------------------------------------------------------------------------------------------------------------
    @commands.command()
    @commands.bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True)
    @commands.has_permissions(manage_channels=True)
    async def update(self, ctx):
        if ctx.guild is None:
            await ctx.send("This command cannot be used in a DM channel.")
            return
    
        if ctx.guild.id in univ.Directories.keys():
            await ctx.message.delete()
            await self.update_directory(ctx, "Update requested manually.")
        else:
            await ctx.send(f"You don't have a directory yet. Use the `{BOT_PREFIX}setup` command to create one.")

    #--------------------------------------------------------------------------------------------------------------------------
    @commands.command()
    @commands.bot_has_permissions(send_messages=True, manage_channels=True, manage_messages=True)
    async def invite(self, ctx):
        await ctx.send("Here: https://discord.com/oauth2/authorize?client_id=698965636432265227&permissions=268479504&scope=bot")

    #--------------------------------------------------------------------------------------------------------------------------
    @commands.command(name="help")
    @commands.bot_has_permissions(send_messages=True)
    async def bhelp(self, ctx, section="directory", subsection=None):
        if section.lower() == "directory":
            await ctx.send(f"""
New? Try these commands in your server:
```
{BOT_PREFIX}setup
{BOT_PREFIX}new_channel "root" "Front Yard"
{BOT_PREFIX}new_category "root" "Big House"
{BOT_PREFIX}new_channel "root//Big House" "Livingroom"
```
Required Permissions:
```
"Manage Roles"    - To set the directory channel so that only the server owner may use it until further permissions are set.
"Manage Channels" - To create new channels.
"Manage Messages" - To manage the directory channel so that it's kept clean.
"Read Messages"   - To read commands.
"Send Messages"   - To send notifications/messages for warnings, confirmations, etc.
"Attach Files"    - To send the requested file from the command {BOT_PREFIX}save_directory.
```
To see important announcements and command changes, Type and enter `{BOT_PREFIX}help updates`
Use this if you think a command isn't working the same way it did last time you used it.

--------------------------------------------------

Type `{BOT_PREFIX}help <directory>`, where `directory` is one of the following:
**Details**
**Commands**
""")

        elif section.lower() == "details":
            owner = await bot.fetch_user(bot.owner_id)
            await ctx.send(f"""
**Details:**
Command prefix: `{BOT_PREFIX}`
Create a custom directory to better organize your channels.

This bot was created by: {owner.name+"#"+owner.discriminator}
Support Server invite: https://discord.gg/j2y7jxQ
Warning: Support server may contain swearing in open channels.
*Consider DMing the developer instead for questions/information.

Number of servers this bot is in now: {len(bot.guilds)}
:asterisk: Number of servers using the new directory system: {len(univ.Directories.keys())}
""")
            
        elif section.lower() == "commands":
            if subsection == None:
                await ctx.send(f"""
**Commands**
Type `{BOT_PREFIX}help commands <command>`, where `command` is one of the following:
```
Directory -- Control the directory setup
    setup             - You require the "Manage Server" and "M/Channels" permissions.
    teardown          - You require the "Manage Server" and "M/Channels" permissions.

Channels -- Manage channels in the directory
    create_channel    - You require the "Manage Channels" permission.
    create_category   - You require the "Manage Channels" permission.
    delete_category   - You require the "Manage Channels" permission.
    rename_channel    - You require the "Manage Channels" permission.
    move_channel      - You require the "Manage Channels" permission.
    import_channel    - You require the "Manage Channels" permission.
    hide_channel      - You require the "Manage Channels" permission.
    save_directory    - No Limits
    update            - You require the "Manage Channels" permission.

General -- General commands
    help              - No Limits
    invite            - No Limits
```
""")
            elif subsection.lower() == "setup":
                await ctx.send(f"""
**SETUP**; Aliases: "su"
`{BOT_PREFIX}setup`
------------------------------
Set up your new custom directory system.
**--** Attaching a cdr_directory.pkl file with proper contents generated by the `{BOT_PREFIX}save_directory` command will load an existing directory based on that file.
**--** You should never delete the category created by the bot. Doing this will disorganize potentially hundreds of channels under it.
**----** Do prevent these inconveniences that I should be worried about, use the `{BOT_PREFIX}teardown` command. I'll handle everything.
""")

            elif subsection.lower() == "teardown":
                await ctx.send(f"""
**TEARDOWN**; Aliases: "td"
`{BOT_PREFIX}teardown`
------------------------------
Deconstruct the custom directory system added to your server, provided by me.
**--** IMPORTANT! Use this command especially if you have a lot of channels under the category that I created.
""")

            elif subsection.lower() == "new_channel":
                await ctx.send(f"""
**CREATE_CHANNEL**; Aliases: "new_ch"
`{BOT_PREFIX}create_channel <directory> <name>`
------------------------------
Create a new channel under `directory` with the name `name`.
**--** It is recommended not to make 2 channels with the same name in the same directory! (This is not allowed by the bot anymore)
**--** To delete a channel, simply nagivate to the channel using the directory (or manually), channel options, and click Delete Channel. The bot will automatically update the directory. If not, use this command:
**----** `{BOT_PREFIX}update`
""")

            elif subsection.lower() == "create_channel":
                await ctx.send(f"""
**CREATE_CATEGORY**; Aliases: "new_cat"
`{BOT_PREFIX}create_category <directory> <name>`
------------------------------
Create a new category under `directory` with the name `name`.
**--** It is recommended not to make 2 categories with the same name in the same directory! (This is not allowed by the bot anymore)
""")

            elif subsection.lower() == "delete_category":
                await ctx.send(f"""
**DELETE_CATEGORY**; Aliases: "del_cat"
`{BOT_PREFIX}delete_category <directory> <name>`
------------------------------
Delete a category, along with all channels within it.
**-- THIS ACTION CANNOT BE UNDONE.**
""")

            elif subsection.lower() == "rename_channel":
                await ctx.send(f"""
**RENAME_CHANNEL**; Aliases: "rn_ch"
`{BOT_PREFIX}rename_channel <directory> <name> <rename>`
------------------------------
Rename the channel at the directory `directory` with name `name` to `rename`.
**--** You cannot rename to a channel already with the same name in the same directory.
""")

            elif subsection.lower() == "move_channel":
                await ctx.send(f"""
**MOVE_CHANNEL**; Aliases: "mv_ch"
`{BOT_PREFIX}move_channel <directory> <name> <new_directory>`
------------------------------
Moves a channel or category at the directory `directory` with name `name` to the directory `new_directory`.
**--** You cannot move a channel or category if the destination already has a channel or category with that name.
""")

            elif subsection.lower() == "import_channel":
                await ctx.send(f"""
**IMPORT_CHANNEL**; Aliases: "imp_ch"
`{BOT_PREFIX}import_channel <channel> <new_directory> <name>`
------------------------------
Imports an existing channel into the directory `new_directory` with the name `name`.
**--** Your channel will not be moved or changed.
**--** You cannot import a channel if the destination already has a channel or category with the name `name`.
""")
            elif subsection.lower() == "hide_channel":
                await ctx.send(f"""
**HIDE_CHANNEL**; Aliases: "hd_ch"
`{BOT_PREFIX}hide_channel <directory> <name>`
------------------------------
Hide an existing channel from the directory `directory` with the name `name`.
**--** Your channel will not be moved, changed, or deleted.
**--** To make it appear again, use the `import_channel` command to import it back in a directory.
""")
            elif subsection.lower() == "save_directory":
                await ctx.send(f"""
**SAVE_DIRECTORY**; Aliases: "save"
`{BOT_PREFIX}save_directory`
------------------------------
Save your current directory setup to a file to be loaded later at any time.
**--** This file contains pickled data using Python.
**--** To load said file, use the `{BOT_PREFIX}setup` command and attach the file to proceed.
**----** The process takes longer depending on how many channels are in the entire directory.
""")
            elif subsection.lower() == "update":
                await ctx.send(f"""
**UPDATE**
`{BOT_PREFIX}update`
------------------------------
Updates the directory channel.
**--** The more channels in the directory, the longer it takes to finish.
**----** During this time, no changes can be made to the directory.

**--** This command is automatically called when any channel in your server is deleted.
**----** If channels are being deleted faster than the bot can update, you may have to update it manually when you are done.

**--** The more channels that are deleted when calling this command, the longer it takes to finish.
**----** The system works by checking if a channel exists. If not, it updates internal memory and restarts.
""")

            elif subsection.lower() == "help":
                await ctx.send(f"""
**HELP**
`{BOT_PREFIX}help [section] [subsection]`
------------------------------
Sends a help message.
**--** The `section` and `subsection` arguments:
**----** Typing `{BOT_PREFIX}help` will give you `section` names.
**----** If `section` is "commands", `subsection` help on a certain command.
""")

            elif subsection.lower() == "invite":
                await ctx.send(f"""
**INVITE**
`{BOT_PREFIX}invite`
------------------------------
Sends an invite link to let me join a server.
""")
            

        
    #--------------------------------------------------------------------------------------------------------------------------
    @commands.command(name="logout")
    @commands.is_owner()
    async def blogout(self, ctx):
        await ctx.send("Logging out...")
        if not os.path.exists(f"{Dir1}\\Serialized\\data.pkl"):
            await ctx.send("[Unable to save] data.pkl not found. Replace file before shutting down.")
            print("[Unable to save] data.pkl not found. Replace file before shutting down.")
            return

        with open(f"{Dir1}\\Serialized\\data.pkl", "wb") as f:
            try:
                data = univ.Directories
                pickle.dump(data, f)
            except Exception as e:
                await ctx.send("[Unable to save; Data Reset] Pickle dumping Error: "+ str(e))

        await bot.logout()
    
    # Events
    #--------------------------------------------------------------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if isinstance(channel, discord.CategoryChannel):
            try:
                if channel.guild.id not in univ.TearingDown and channel.id == univ.Directories[channel.guild.id]["categoryID"]:
                    try:
                        directory = await bot.fetch_channel(univ.Directories[channel.guild.id]["channelID"])
                    except discord.errors.NotFound:
                        return

                    try:
                        dmessage = await directory.fetch_message(univ.Directories[channel.guild.id]["msgID"])
                    except discord.errors.NotFound:
                        await self.update_directory(channel, note="Repaired directory message.")
                        
                    try: 
                        await dmessage.edit(content="All channels have been disorganized!")
                    except discord.NotFound:
                        pass
                    
                    univ.Directories.pop(channel.guild.id)

                    ch = channel.guild.system_channel
                    if ch is not None:
                        await ch.send(f":anger: Aww, what a mess! Someone messed up my directory! Next time, PLEASE use the command `{BOT_PREFIX}teardown` that I provided you to teardown the directories appropriately. Unfortunately I can't delete all the channels that have been disorganized!")
                else:
                    pass

            except KeyError or discord.errors.NotFound:
                pass

        if channel.guild.id in self.LoadingUpdate.keys():
            if self.LoadingUpdate[channel.guild.id] == False:
                self.LoadingUpdate[channel.guild.id] = True
                try:
                    dchannel = await bot.fetch_channel(univ.Directories[channel.guild.id]["channelID"])
                except discord.errors.NotFound:
                    pass
                else:
                    async with dchannel.typing():
                        await self.update_directory(channel, note="Updated automatically following channel deletion by user.")
                    self.LoadingUpdate[channel.guild.id] = False

    @commands.Cog.listener()
    async def on_ready(self):
        print("Logged in as", bot.user)
        print("ID:", bot.user.id)
        print('------')

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.guild is None:
            return
        
        if msg.author == bot.user:
            return

        verify_command = await bot.get_context(msg)
        if verify_command.valid:
            return
        
        if msg.guild.id in univ.Directories.keys():
            if msg.channel.id == univ.Directories[msg.guild.id]["channelID"]:
                try:
                    await msg.delete()
                except discord.Forbidden:
                    pass

        if bot.user.mentioned_in(msg):
            try:
                if msg.author.id == bot.owner_id:
                    await msg.add_reaction("💕")
                else:
                    await msg.add_reaction("👋")
            except discord.errors.Forbidden:
                pass

    # Errors
    #--------------------------------------------------------------------------------------------------------------------------
    if debug_mode != "D":
      @commands.Cog.listener()
      async def on_command_error(self, ctx, error):
        msg = ctx.message
        if isinstance(error, discord.ext.commands.BotMissingPermissions):
            await ctx.message.delete()
            await msg.author.send(f"This bot is missing one or more permissions listed in `{BOT_PREFIX}permissions`.")
            return

        elif isinstance(error, discord.ext.commands.NotOwner):
            await ctx.message.delete()
            await msg.author.send("That command is not listed in the help menu and is to be used by the owner only.")
            return
        
        elif isinstance(error, discord.ext.commands.MissingRequiredArgument):
            await ctx.message.delete()
            await msg.author.send(f"\"{error.param.name}\" is a required argument that is missing.")
            return
	
        elif isinstance(error, discord.ext.commands.CommandNotFound):
            supposed_command = msg.content.split()[0]
            await ctx.message.delete()
            await msg.author.send(f"Command \"{supposed_command}\" doesn't exist.")
            return

        elif isinstance(error, discord.ext.commands.MissingPermissions):
            await ctx.message.delete()
            await msg.author.send(f"You require the Manage Channels and Manage Server permissions to create and teardown the directory, and to make new channels.")
            return
        
        else:
            if ctx.command.name is not None:
                await ctx.author.send(f"[Error in command \"{ctx.command.name}\"] "+str(error)+f"\nIf you keep getting this error, let the developer know!\nIn the case of a `404 Not Found` error, try using the `{BOT_PREFIX}update` command.")
                print(f"[Error in command \"{ctx.command.name}\"]", str(error))
            else:
                await ctx.author.send(f"[Error outside of command] "+str(error)+"\nIf you keep getting this error, let the developer know!")
                print("[Error outside of command]", error)


#--------------------------------------------------------------


# Run
#--------------------------------------------------------------

bot.add_cog(Background_Tasks(bot))
bot.add_cog(Commands(bot))
bot.run(BOT_TOKEN)

#--------------------------------------------------------------
