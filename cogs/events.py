
# Lib
from asyncio import sleep
from asyncio.exceptions import TimeoutError
from contextlib import suppress
from copy import deepcopy

# Site
from discord import Reaction, Member, Message, Status, Embed
from discord.channel import CategoryChannel
from discord.errors import Forbidden, HTTPException
from discord.ext.commands.cog import Cog
from discord.ext.commands.context import Context
from discord.ext.commands.errors import (
    BotMissingPermissions,
    MissingPermissions,
    CommandNotFound,
    MissingRequiredArgument,
    NotOwner,
    CommandOnCooldown
)

# Local
from utils.classes import Bot
from utils.directory_mgmt import loadingupdate as lucm, recurse_index, usinggui


class Events(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if channel.guild.id not in self.bot.LoadingUpdate and channel.guild.id in self.bot.user_data["Directories"]:
            with lucm(self.bot, channel.guild.id):
                await sleep(5)
                catch_id = deepcopy(self.bot.user_data["Directories"][channel.guild.id]["categoryID"])
                await self.bot.update_directory(channel,
                                                note="Updated automatically following channel deletion by user.")
                if isinstance(channel, CategoryChannel) and channel.id == catch_id:
                    async def recurse_move_channels(d: dict):
                        for key, val in d.items():
                            if isinstance(val, tuple):
                                ch = self.bot.get_channel(val[0])
                                dcategory = self.bot.get_channel(
                                    self.bot.user_data["Directories"][channel.guild.id]["categoryID"])
                                if ch and not val[1]:
                                    await ch.edit(category=dcategory)
                            elif isinstance(val, dict):
                                await recurse_move_channels(d[key])
                            else:
                                raise ValueError("Invalid directory dictionary passed.")

                    await recurse_move_channels(self.bot.user_data["Directories"][channel.guild.id]["tree"])

    @Cog.listener()
    async def on_message(self, msg: Message):
        if msg.author.bot:
            return

        if msg.author.id == 726313554717835284:
            ids = msg.content.split(";")
            voter = int(ids[0])
            voted_for = int(ids[1])

            if voted_for == self.bot.user.id:  # append `or 687427956364279873` for testing instance
                user = await self.bot.fetch_user(voter)
                try:
                    await user.send(
                        "Thanks for voting! You will now have access to the following commands shortly for 12 hours:\n"
                        "```\n"
                        f"{self.bot.command_prefix}add_to_closet\n"
                        f"{self.bot.command_prefix}remove_from_closet\n"
                        f"{self.bot.command_prefix}rename_closet_entry\n"
                        f"{self.bot.command_prefix}see_closet\n"
                        f"{self.bot.command_prefix}preview_closet_entry\n"
                        f"```\n"
                        f"These commands allow you to store favorite vanity avatars "
                        f"and use them anywhere. You can only hold up to 10.\n"
                        f"For help on the usage of each command, "
                        f"enter `{self.bot.command_prefix}help commands <command name>`.")

                except HTTPException or Forbidden:
                    print(f"[❌] User \"{user}\" voted for \"{self.bot.user}\". DM Failed.")
                else:
                    print(f"[] User \"{user}\" voted for \"{self.bot.user}\".")

                return

        # Check if the message is a command. Terminates the event if so, so the command can run.
        verify_command = await self.bot.get_context(msg)
        if verify_command.valid:
            self.bot.inactive = 0
            return

        # Support can be run through DMs
        if msg.guild is None:
            if msg.author.id != self.bot.owner_ids[0]:
                if msg.content.startswith("> "):
                    if msg.author.id not in self.bot.config['muted_dms']:
                        if msg.author.id in self.bot.waiting:
                            await msg.channel.send(":clock9: Please wait, you already have a question open.\n"
                                                   "You'll get a response from me soon.")

                            return

                        dev_guild = self.bot.get_guild(699399549218717707)  # Developer's Guild
                        user = dev_guild.get_member(self.bot.owner_ids[0])
                        if user.status == Status.dnd:
                            await msg.channel.send(":red_circle: The developer currently has "
                                                   "Do Not Disturb on. Please try again later.")
                            return
                        elif user.status == Status.idle:
                            conf = await msg.channel.send(":orange_circle: The developer is currently idle, "
                                                          "are you sure you want to send?\n"
                                                          "Sending `Yes` will send the message, but you *may* not get a response.\n"
                                                          "(`Yes`, `No`)")

                            def check(m):
                                return m.content.lower() in ["yes", "no"]
                            try:
                                message = await self.bot.wait_for("message", timeout=20, check=check)
                            except TimeoutError:
                                await conf.edit(":orange_circle: The developer is currently idle, "
                                                "are you sure you want to send?\n"
                                                "Sending `Yes` will send the message, but you *may* not get a response.\n"
                                                "(`Yes`, `No`)")
                            else:
                                if message.content == "no":
                                    return await conf.edit(":orange_circle: The developer is currently idle.\n"
                                                           "Please try again later.")

                                elif message.content == "yes":
                                    await conf.delete()

                        status_msg = await msg.channel.send(":clock9: "
                                                            "I sent your message to the developer.\n"
                                                            "Please stand by for a response or "
                                                            "until **this message is edited**...\n")

                        self.bot.waiting.append(msg.author.id)

                        embed = Embed(color=0xff87a3)
                        embed.title = f"Message from user {msg.author} (ID: {msg.author.id}):"
                        embed.description = f"{msg.content}\n\n" \
                                            f"Replying to this DM **within 120 seconds** " \
                                            f"after accepting **within 10 minutes** " \
                                            f"will relay the message back to the user."

                        dm = await user.send(content="**PENDING**", embed=embed)
                        await dm.add_reaction("✅")
                        await dm.add_reaction("❎")

                        def check(sreaction, suser):
                            if self.bot.thread_active:
                                self.bot.loop.create_task(
                                    reaction.channel.send("There is already an active thread running...\n "
                                                          "Please finish the **`ACTIVE`** one first."))
                                return False
                            else:
                                return sreaction.message.id == dm.id and \
                                    str(sreaction.emoji) in ["✅", "❎"] and \
                                    suser == user
                        try:
                            reaction, user = await self.bot.wait_for("reaction_add", timeout=600, check=check)
                        except TimeoutError:
                            await dm.edit(content="**TIMED OUT**")
                            await status_msg.edit(content=":x: "
                                                          "The developer is unavailable right now. Try again later.")
                            return
                        else:
                            if str(reaction.emoji) == "❎":
                                await dm.edit(content="**DENIED**")
                                await status_msg.edit(content=":information_source: The developer denied your message. "
                                                              "Please make sure you are as detailed as possible.")
                                return
                            elif str(reaction.emoji) == "✅":
                                await dm.edit(content="**ACTIVE**")
                                await status_msg.edit(content=":information_source: "
                                                              "The developer is typing a message back...")
                                self.bot.thread_active = True
                                pass

                        def check(mmessage):
                            return mmessage.author == user and mmessage.channel == dm.channel
                        while True:

                            try:
                                response = await self.bot.wait_for("message", timeout=120, check=check)
                            except TimeoutError:
                                conf = await user.send(":warning: Press the button below to continue typing.")
                                await conf.add_reaction("🔘")

                                def conf_button(b_reaction, b_user):
                                    return str(b_reaction.emoji) == "🔘" and b_user == user \
                                           and b_reaction.message.channel == dm.channel

                                try:
                                    await self.bot.wait_for("reaction_add", timeout=10, check=conf_button)
                                except TimeoutError:
                                    await conf.delete()
                                    await dm.edit(content="**TIMED OUT**")
                                    await dm.channel.send("You timed out. "
                                                          "The user was notified that you are not available right now.")

                                    self.bot.waiting.remove(msg.author.id)
                                    self.bot.thread_active = False
                                    await status_msg.edit(content=":information_source: "
                                                                  "The developer timed out on typing a response. "
                                                                  "Please ask at a later time.\n"
                                                                  "You may also join the support server here: "
                                                                  "https://discord.gg/j2y7jxQ")
                                    return
                                else:
                                    await conf.delete()
                                    continue
                            else:
                                self.bot.waiting.remove(msg.author.id)
                                self.bot.thread_active = False
                                await dm.edit(content="**Answered**")
                                await dm.channel.send(":white_check_mark: Okay, message sent.")
                                await status_msg.edit(content=":white_check_mark: The developer has responded.")
                                await msg.channel.send(f":newspaper: Response from the developer:\n{response.content}")
                                return
                    else:
                        await msg.channel.send("You've been muted by the developer, "
                                               "so you cannot send anything.\n"
                                               "If you believe you were muted by mistake, "
                                               "please join the support server:\n"
                                               "https://discord.gg/j2y7jxQ\n\n"
                                               "**Note that spamming will get you banned without hesitation.**")
                        return
                else:
                    await msg.channel.send("Please start your message with "
                                           "\"`> `\" "
                                           "to ask a question or send compliments.\n"
                                           "This is the markdown feature to create quotes.",
                                           delete_after=5)
                    return
            return

        if msg.guild.id in self.bot.user_data["Directories"]:
            if msg.channel.id == self.bot.user_data["Directories"][msg.guild.id]["channelID"]:
                try:
                    await msg.delete()
                except Forbidden:
                    pass

    @Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, user: Member):
        if reaction.message.guild and reaction.message.guild.id in self.bot.user_data["Directories"]:
            if reaction.message.id == self.bot.user_data["Directories"][reaction.message.guild.id]["messageID"]:
                if reaction.message.guild.id in self.bot.pause_reaction_listening:
                    return

                if user == self.bot.user:
                    return
                else:
                    try:
                        await reaction.remove(user)
                    except Forbidden:
                        await reaction.message.channel.send(f"**{user}**, I can't let you use the GUI because "
                                                            f"I don't have the `Manage Messages` permission!",
                                                            delete_after=5)
                        return

                # Check permissions for the user and bot
                dcategory = self.bot.get_channel(self.bot.user_data["Directories"][reaction.message.guild.id]["categoryID"])
                bot_perms = reaction.message.guild.me.permissions_in(dcategory)
                perms = user.permissions_in(reaction.message.channel)

                # Check if the GUI is already in use, one at a time
                if reaction.message.guild.id in self.bot.using_gui:
                    if self.bot.using_gui[reaction.message.guild.id] == user.id:
                        await reaction.message.channel.send(
                            f"**{user}**, please answer the prompt first!",
                            delete_after=5
                        )
                        return
                    else:
                        user_inuse = self.bot.get_user(self.bot.using_gui[reaction.message.guild.id])
                        await reaction.message.channel.send(
                            f"{user.mention}, **{user_inuse}** is currently using the GUI.",
                            delete_after=5
                        )
                        return

                # Begin operation
                with usinggui(self.bot, reaction.message.guild.id, user.id):
                    if not perms.manage_channels:
                        return await reaction.message.channel.send(f"**{user}**, You require the "
                                                                   f"`Manage Channels` permission to use the GUI.")
                    if str(reaction.emoji) == "📝":
                        await reaction.message.clear_reactions()

                        info = await reaction.message.channel.send("Please wait, loading editor controls...")

                        await reaction.message.add_reaction("1️⃣")
                        await reaction.message.add_reaction("2️⃣")
                        await reaction.message.add_reaction("3️⃣")
                        await reaction.message.add_reaction("4️⃣")
                        await reaction.message.add_reaction("5️⃣")
                        await reaction.message.add_reaction("6️⃣")
                        await reaction.message.add_reaction("7️⃣")

                        await info.edit(
                            content=f"**{user}**\n"
                                    "```\n"
                                    "1️⃣ = Create Channel\n"
                                    "2️⃣ = Create Category\n"
                                    "3️⃣ = Delete Category\n"
                                    "4️⃣ = Rename Category/Channel\n"
                                    "5️⃣ = Move Category/Channel\n"
                                    "6️⃣ = Import Channel\n"
                                    "7️⃣ = Hide Category/Channel\n"
                                    "```"
                        )
                    else:
                        return

                    def check_react(rreaction, uuser):
                        if str(rreaction.emoji) not in ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]:
                            self.bot.loop.create_task(reaction.remove(user))

                        return str(rreaction.emoji) in ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"] and \
                            rreaction.message == reaction.message and \
                            uuser == user

                    self.bot.pause_reaction_listening.append(reaction.message.guild.id)
                    # Pause listening
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=15, check=check_react)
                    except TimeoutError:
                        self.bot.pause_reaction_listening.remove(reaction.message.guild.id)
                        await reaction.message.clear_reactions()
                        await info.edit(content=f":x: **{user}** timed out.", delete_after=5)
                        await reaction.message.add_reaction("📝")
                        await reaction.message.add_reaction("🔄")

                    else:
                        self.bot.pause_reaction_listening.remove(reaction.message.guild.id)
                        await reaction.message.clear_reactions()
                        await info.delete()

                        def check(msg):
                            return msg.author == user and msg.channel == reaction.message.channel

                        if str(reaction.emoji) == "1️⃣":
                            if not all((
                                bot_perms.manage_channels,
                                bot_perms.read_messages,
                                bot_perms.send_messages,
                                bot_perms.manage_messages
                            )):
                                await reaction.message.add_reaction("📝")
                                await reaction.message.add_reaction("🔄")
                                await user.send(
                                    f"Every command requires the `Read Text Channels/Messages`, "
                                    f"`Send Messages` and `Manage Messages` permissions.\n"
                                    f"The `create_channel` command also requires following permissions:\n"
                                    f"```\n"
                                    f"Manage Channels - To create new channels using the new channel system.\n"
                                    f"```"
                                )
                                return

                            confirmation = await reaction.message.channel.send(
                                f"**{user}**\n"
                                f"[60 seconds] Enter the path where you would like to create this channel:\n"
                                f"Path: \\_\\_\\_\\_\n"
                                f"Name: \\_\\_\\_\\_\n"
                                f"Type \"+Cancel\" to cancel.")

                            while True:
                                try:
                                    path = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.",
                                                                   delete_after=5)

                                else:
                                    if path.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                       delete_after=5)

                                    try:
                                        get_item = recurse_index(
                                            self.bot.user_data["Directories"][reaction.message.guild.id]['tree'],
                                            path.content.split("//"))

                                        if isinstance(get_item, int):
                                            raise KeyError(str(path[-1]))

                                    except KeyError as e:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] "
                                                    f"Enter the path where you would like to create this channel:\n"
                                                    f"Path: \\_\\_\\_\\_\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: That directory doesn't exist. "
                                                    f"Level `{e}` is not found.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue
                                    else:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name of your new channel:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        break

                            while True:
                                try:
                                    name = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.",
                                                                   delete_after=5)
                                else:
                                    if name.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                       delete_after=5)

                                    get_item = recurse_index(
                                        self.bot.user_data["Directories"][reaction.message.guild.id]['tree'],
                                        path.content.split("//"))

                                    if isinstance(get_item, dict) and name.content in get_item:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name of your new channel:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: A category/channel with that name "
                                                    f"already exists in that directory.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue

                                    if len(name.content) > 50:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name of your new channel:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: Your name cannot exceed 50 characters in length.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue

                                    else:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"Done! One moment...\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: __{name.content}__\n"
                                        )
                                        await sleep(2)
                                        await confirmation.edit(content="Adding new channel...")
                                        ctx = await self.bot.get_context(reaction.message)
                                        await self.bot.get_command("create_channel").callback(self, ctx,
                                                                                              path.content,
                                                                                              name.content
                                                                                              )
                                        await confirmation.delete()
                                        break

                        elif str(reaction.emoji) == "2️⃣":
                            if not all((
                                bot_perms.read_messages,
                                bot_perms.send_messages,
                                bot_perms.manage_messages
                            )):
                                await reaction.message.add_reaction("📝")
                                await reaction.message.add_reaction("🔄")
                                await user.send(
                                    f"Every command requires the `Read Text Channels/Messages`, "
                                    f"`Send Messages` and `Manage Messages` permissions.\n"
                                    f"The `create_category` command requires no additional permissions."
                                )
                                return
                                
                            confirmation = await reaction.message.channel.send(
                                f"**{user}**\n"
                                f"[60 seconds] Enter the path where you would like to create this category:\n"
                                f"Path: \\_\\_\\_\\_\n"
                                f"Name: \\_\\_\\_\\_\n"
                                f"Type \"+Cancel\" to cancel.")

                            while True:
                                try:
                                    path = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.",
                                                                   delete_after=5)
                                else:
                                    if path.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                       delete_after=5)

                                    try:
                                        get_item = recurse_index(
                                            self.bot.user_data["Directories"][reaction.message.guild.id]['tree'],
                                            path.content.split("//"))

                                        if isinstance(get_item, int):
                                            raise KeyError(str(path[-1]))

                                    except KeyError as e:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] "
                                                    f"Enter the path where you would like to create this category:\n "
                                                    f"Path: \\_\\_\\_\\_\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: That directory doesn't exist. "
                                                    f"Level `{e}` is not found.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue
                                    else:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name of your new category:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        break

                            while True:
                                try:
                                    name = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.",
                                                                   delete_after=5)
                                else:
                                    if name.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                       delete_after=5)

                                    get_item = recurse_index(
                                        self.bot.user_data["Directories"][reaction.message.guild.id]['tree'],
                                        path.content.split("//"))

                                    if name.content in get_item:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name of your new category:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: A category/channel with that name "
                                                    f"already exists in that directory.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue

                                    if len(name.content) > 50:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name of your new category:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: Your name cannot exceed 50 characters in length.\n"
                                                    f"Type \"+Cancel\" to cancel."
                                        )
                                        continue

                                    else:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"Done! One moment...\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: __{name.content}__\n")

                                        await sleep(2)
                                        await confirmation.edit(content="Adding new category...")
                                        ctx = await self.bot.get_context(reaction.message)
                                        await self.bot.get_command("create_category").callback(self, ctx,
                                                                                               path.content,
                                                                                               name.content
                                                                                               )
                                        await confirmation.delete()
                                        break

                        elif str(reaction.emoji) == "3️⃣":
                            if not all((
                                bot_perms.manage_channels,
                                bot_perms.read_messages,
                                bot_perms.send_messages,
                                bot_perms.manage_messages
                            )):
                                await reaction.message.add_reaction("📝")
                                await reaction.message.add_reaction("🔄")
                                await user.send(
                                    f"Every command requires the `Read Text Channels/Messages`, "
                                    f"`Send Messages` and `Manage Messages` permissions.\n"
                                    f"The `delete_category` command also requires following permissions:\n"
                                    f"```\n"
                                    f"Manage Channels - To delete channels under a V2* category.\n"
                                    f"```\n"
                                    f"\\* A V2 category is a category created by me, "
                                    f"and is not associated with Discord. "
                                    f"It is involved with the new system."
                                )
                                return

                            confirmation = await reaction.message.channel.send(
                                f"**{user}**\n"
                                f"[60 seconds] Enter the path where you would like to delete a category:\n"
                                f"Path: \\_\\_\\_\\_\n"
                                f"Name: \\_\\_\\_\\_\n"
                                f"Type \"+Cancel\" to cancel.")

                            while True:
                                try:
                                    path = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                   delete_after=5)
                                else:
                                    if path.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                       delete_after=5)

                                    try:
                                        get_item = recurse_index(
                                            self.bot.user_data["Directories"][reaction.message.guild.id]['tree'],
                                            path.content.split("//"))

                                        if isinstance(get_item, int):
                                            raise KeyError(str(path[-1]))

                                    except KeyError as e:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] "
                                                    f"Enter the path where you would like to delete a category:\n "
                                                    f"Path: \\_\\_\\_\\_\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: That directory doesn't exist. "
                                                    f"Level `{e}` is not found.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue
                                    else:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name of the target category:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        break

                            while True:
                                try:
                                    name = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.",
                                                                   delete_after=5)
                                else:
                                    if name.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                       delete_after=5)

                                    get_item = recurse_index(
                                        self.bot.user_data["Directories"][reaction.message.guild.id]['tree'],
                                        path.content.split("//"))

                                    if isinstance(get_item, dict) and name.content not in get_item:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name of the target category:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: A category with that name "
                                                    f"doesn't exist in that directory.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue

                                    elif isinstance(get_item[name.content], tuple):
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name of the target category:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: That's a channel, not a category. "
                                                    f"Navigate to the channel to delete it manually.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue

                                    if len(name.content) > 50:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name of the target category:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: Your name cannot exceed 50 characters in length.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue

                                    else:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"Done! One moment...\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: __{name.content}__\n"
                                        )
                                        await sleep(2)
                                        await confirmation.edit(content="Deleting category...")
                                        ctx = await self.bot.get_context(reaction.message)
                                        await self.bot.get_command("delete_category").callback(self, ctx,
                                                                                               path.content,
                                                                                               name.content
                                                                                               )
                                        await confirmation.delete()
                                        break

                        elif str(reaction.emoji) == "4️⃣":
                            if not all((
                                bot_perms.manage_channels,
                                bot_perms.read_messages,
                                bot_perms.send_messages,
                                bot_perms.manage_messages
                            )):
                                await reaction.message.add_reaction("📝")
                                await reaction.message.add_reaction("🔄")
                                await user.send(
                                    f"Every command requires the `Read Text Channels/Messages`, "
                                    f"`Send Messages` and `Manage Messages` permissions.\n"
                                    f"The `rename_channel` command also requires following permissions:\n"
                                    f"```\n"
                                    f"Manage Channels - To rename channels created with the new system.\n"
                                    f"```\n"
                                    f"This command can also rename V2\\* categories.\n"
                                    f"\\* A V2 category is a category created by me, "
                                    f"and is not associated with Discord."
                                )

                            confirmation = await reaction.message.channel.send(
                                f"**{user}**\n"
                                f"[60 seconds] Enter the path where you would like to rename a category or channel:\n"
                                f"Path: \\_\\_\\_\\_\n"
                                f"Name: \\_\\_\\_\\_\n"
                                f"Rename: \\_\\_\\_\\_\n"
                                f"Type \"+Cancel\" to cancel.")

                            while True:
                                try:
                                    path = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.",
                                                                   delete_after=5)
                                else:
                                    if path.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                       delete_after=5)

                                    try:
                                        get_item = recurse_index(
                                            self.bot.user_data["Directories"][reaction.message.guild.id]['tree'],
                                            path.content.split("//"))

                                        if isinstance(get_item, int):
                                            raise KeyError(str(path[-1]))

                                    except KeyError as e:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Enter the path where you would "
                                                    f"like to rename a category or channel:\n "
                                                    f"Path: \\_\\_\\_\\_\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f"Rename: \\_\\_\\_\\_\n"
                                                    f":warning: That directory doesn't exist. "
                                                    f"Level `{e}` is not found.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue
                                    else:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the the target's name:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f"Rename: \\_\\_\\_\\_\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        break

                            while True:
                                try:
                                    name = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.",
                                                                   delete_after=5)
                                else:
                                    if name.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                       delete_after=5)

                                    get_item = recurse_index(
                                        self.bot.user_data["Directories"][reaction.message.guild.id]['tree'],
                                        path.content.split("//"))

                                    if name.content not in get_item:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the the target's name:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f"Rename: \\_\\_\\_\\_\n"
                                                    f":warning: A category/channel with that name "
                                                    f"doesn't exist in that directory.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue

                                    if len(name.content) > 50:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the the target's name:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f"Rename: \\_\\_\\_\\_\n"
                                                    f":warning: Your name cannot exceed 50 characters in length.\n"
                                                    f"Type \"+Cancel\" to cancel."
                                        )
                                        continue

                                    else:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the the target's **new** name:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: __{name.content}__\n"
                                                    f"Rename: \\_\\_\\_\\_\\_\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        break

                            while True:
                                try:
                                    rename = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                   delete_after=5)
                                else:
                                    if rename.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                       delete_after=5)

                                    get_item = recurse_index(
                                        self.bot.user_data["Directories"][reaction.message.guild.id]['tree'],
                                        path.content.split("//"))

                                    if rename.content in get_item:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the the target's **new** name:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: __{name.content}__\n"
                                                    f"Rename: \\_\\_\\_\\_\n"
                                                    f":warning: A category/channel with that name "
                                                    f"already exists in that directory.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue

                                    if len(rename.content) > 50:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the the target's **new** name:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: __{name.content}__\n"
                                                    f"Rename: \\_\\_\\_\\_\n"
                                                    f":warning: Your new name cannot exceed 50 characters in length.\n"
                                                    f"Type \"+Cancel\" to cancel."
                                        )
                                        continue

                                    else:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"Done! One moment...\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: __{name.content}__\n"
                                                    f"Rename: __{rename.content}__\n")

                                        await sleep(2)
                                        await confirmation.edit(content="Renaming category/channel...")
                                        ctx = await self.bot.get_context(reaction.message)
                                        await self.bot.get_command("rename_channel").callback(self, ctx,
                                                                                              path.content,
                                                                                              name.content,
                                                                                              rename.content
                                                                                              )
                                        await confirmation.delete()
                                        break

                        elif str(reaction.emoji) == "5️⃣":
                            if not all((
                                bot_perms.read_messages,
                                bot_perms.send_messages,
                                bot_perms.manage_messages
                            )):
                                await reaction.message.add_reaction("📝")
                                await reaction.message.add_reaction("🔄")
                                await user.send(
                                    f"Every command requires the `Read Text Channels/Messages`, "
                                    f"`Send Messages` and `Manage Messages` permissions.\n"
                                    f"The `move_channel` command requires no additional permissions."
                                )

                            confirmation = await reaction.message.channel.send(
                                f"**{user}**\n"
                                f"[60 seconds] Enter the path where you would like to move a category or channel:\n"
                                f"Path: \\_\\_\\_\\_\n"
                                f"Name: \\_\\_\\_\\_\n"
                                f"New Path: \\_\\_\\_\\_\n"
                                f"Type \"+Cancel\" to cancel.")

                            while True:
                                try:
                                    path = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.",
                                                                   delete_after=5)
                                else:
                                    if path.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                       delete_after=5)

                                    try:
                                        get_item = recurse_index(
                                            self.bot.user_data["Directories"][reaction.message.guild.id]['tree'],
                                            path.content.split("//"))

                                        if isinstance(get_item, int):
                                            raise KeyError(str(path[-1]))

                                    except KeyError as e:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Enter the path where you would "
                                                    f"like to move a category or channel:\n "
                                                    f"Path: \\_\\_\\_\\_\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f"New Path: \\_\\_\\_\\_\n"
                                                    f":warning: That directory doesn't exist. "
                                                    f"Level `{e}` is not found.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue
                                    else:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the the target's name:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f"New Path: \\_\\_\\_\\_\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        break

                            while True:
                                try:
                                    name = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.",
                                                                   delete_after=5)
                                else:
                                    if name.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                       delete_after=5)

                                    get_item = recurse_index(
                                        self.bot.user_data["Directories"][reaction.message.guild.id]['tree'],
                                        path.content.split("//"))

                                    if name.content not in get_item:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the the target's name:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f"New Path: \\_\\_\\_\\_\n"
                                                    f":warning: A category/channel with that name "
                                                    f"doesn't exist in that directory.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue

                                    if len(name.content) > 50:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the the target's name:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f"New Path: \\_\\_\\_\\_\n"
                                                    f":warning: Your name cannot exceed 50 characters in length.\n"
                                                    f"Type \"+Cancel\" to cancel."
                                        )
                                        continue

                                    else:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the the target's **new** path:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: __{name.content}__\n"
                                                    f"New Path: \\_\\_\\_\\_\\_\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        break

                            while True:
                                try:
                                    new_path = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                   delete_after=5)
                                else:
                                    if new_path.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                       delete_after=5)

                                    try:
                                        get_new_item = recurse_index(
                                            self.bot.user_data["Directories"][reaction.message.guild.id]['tree'],
                                            new_path.content.split("//"))

                                        if isinstance(get_new_item, int):
                                            raise KeyError(str(path[-1]))

                                    except KeyError as e:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the the target's **new** path:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: __{name.content}__\n"
                                                    f"New Path: \\_\\_\\_\\_\n"
                                                    f":warning: Your destination path doesn't exist. "
                                                    f"Level `{e}` is not found.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue
                                    else:
                                        if name.content in get_new_item:
                                            await confirmation.edit(
                                                content=f"**{user}**\n"
                                                        f"[60 seconds] Now, enter the the target's **new** path:\n"
                                                        f"Path: __{path.content}__\n"
                                                        f"Name: __{name.content}__\n"
                                                        f"New Path: \\_\\_\\_\\_\n"
                                                        f":warning: A category/channel already has the same name "
                                                        f"as your target. Rename either channel and try again.\n"
                                                        f"Type \"+Cancel\" to cancel.")
                                            continue
                                        else:
                                            await confirmation.edit(
                                                content=f"**{user}**\n"
                                                        f"Done! One moment...\n"
                                                        f"Path: __{path.content}__\n"
                                                        f"Name: __{name.content}__\n"
                                                        f"New Path: __{new_path.content}__\n")

                                            await sleep(2)
                                            await confirmation.edit(content="Renaming category/channel...")
                                            ctx = await self.bot.get_context(reaction.message)
                                            await self.bot.get_command("move_channel").callback(self, ctx,
                                                                                                path.content,
                                                                                                name.content,
                                                                                                new_path.content
                                                                                                )
                                            await confirmation.delete()
                                            break

                        elif str(reaction.emoji) == "6️⃣":
                            if not all((
                                bot_perms.read_messages,
                                bot_perms.send_messages,
                                bot_perms.manage_messages
                            )):
                                await reaction.message.add_reaction("📝")
                                await reaction.message.add_reaction("🔄")
                                await user.send(
                                    f"Every command requires the `Read Text Channels/Messages`, "
                                    f"`Send Messages` and `Manage Messages` permissions.\n"
                                    f"The `import_channel` command requires no additional permissions."
                                )

                            confirmation = await reaction.message.channel.send(
                                f"**{user}**\n"
                                f"[60 seconds] Mention the channel you would like to import:\n"
                                f"Channel: \\_\\_\\_\\_\n"
                                f"Path: \\_\\_\\_\\_\n"
                                f"Name: \\_\\_\\_\\_\n"
                                f"Type \"+Cancel\" to cancel.")

                            while True:
                                try:
                                    channel = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.",
                                                                   delete_after=5)
                                else:
                                    if channel.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                       delete_after=5)

                                    channel_id = int(channel.content.replace("<#", "").replace(">", ""))

                                    channel_found = self.bot.get_channel(channel_id)

                                    if not channel_found:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Mention the channel you would like to import:\n "
                                                    f"Channel: \\_\\_\\_\\_\n"
                                                    f"Path: \\_\\_\\_\\_\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: That channel doesn't exist.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue

                                    tree = deepcopy(self.bot.user_data["Directories"][reaction.message.guild.id]["tree"])
                                    while True:
                                        ids = self.bot.get_all_ids(tree, c_ids=list())
                                        if isinstance(ids, dict):
                                            tree = ids
                                            continue
                                        elif isinstance(ids, list):
                                            break

                                    if channel_found.id in [cid[0] for cid in ids]:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name to import this channel as:\n"
                                                    f"Channal: \\_\\_\\_\\_\n"
                                                    f"Path: \\_\\_\\_\\_\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: That channel is already in the directory. "
                                                    f"It was either created with the new system, "
                                                    f"or already imported.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue

                                    await confirmation.edit(
                                        content=f"**{user}**\n"
                                                f"[60 seconds] Now, enter the path you would "
                                                f"like to import this channel into:\n"
                                                f"Channel: __{channel_found.mention}__\n"
                                                f"Path: \\_\\_\\_\\_\n"
                                                f"Name: \\_\\_\\_\\_\n"
                                                f"Type \"+Cancel\" to cancel.")
                                    break

                            while True:
                                try:
                                    path = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.",
                                                                   delete_after=5)
                                else:
                                    if path.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                       delete_after=5)

                                    try:
                                        recurse_index(
                                            self.bot.user_data["Directories"][reaction.message.guild.id]['tree'],
                                            path.content.split("//"))
                                    except KeyError as e:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the path you would "
                                                    f"like to import this channel into:\n"
                                                    f"Channel: __{channel_found.mention}__\n"
                                                    f"Path: \\_\\_\\_\\_\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: That directory doesn't exist. Level `{e}` not found.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue

                                    else:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name to import this channel as:\n"
                                                    f"Channal: __{channel_found.mention}__\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        break

                            while True:
                                try:
                                    name = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                   delete_after=5)
                                else:
                                    if name.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                       delete_after=5)

                                    get_item = recurse_index(
                                        self.bot.user_data["Directories"][reaction.message.guild.id]['tree'],
                                        path.content.split("//"))

                                    if name.content in get_item:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name to import this channel as:\n"
                                                    f"Channal: __{channel_found.mention}__\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: A category/channel already exists with that name.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue

                                    else:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"Done! One moment...\n"
                                                    f"Channel: __{channel_found.mention}__\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: __{name.content}__\n")

                                        await sleep(2)
                                        await confirmation.edit(content="Importing channel...")
                                        ctx = await self.bot.get_context(reaction.message)
                                        await self.bot.get_command("import_channel").callback(self, ctx,
                                                                                              channel_found,
                                                                                              path.content,
                                                                                              name.content
                                                                                              )
                                        await confirmation.delete()
                                        break

                        elif str(reaction.emoji) == "7️⃣":
                            if not all((
                                bot_perms.read_messages,
                                bot_perms.send_messages,
                                bot_perms.manage_messages
                            )):
                                await reaction.message.add_reaction("📝")
                                await reaction.message.add_reaction("🔄")
                                await user.send(
                                    f"Every command requires the `Read Text Channels/Messages`, "
                                    f"`Send Messages` and `Manage Messages` permissions.\n"
                                    f"The `hide_channel` command requires no additional permissions."
                                )

                            confirmation = await reaction.message.channel.send(
                                f"**{user}**\n"
                                f"[60 seconds] Enter the path where channel you want to hide is located:\n"
                                f"Path: \\_\\_\\_\\_\n"
                                f"Name: \\_\\_\\_\\_\n"
                                f"Type \"+Cancel\" to cancel.")

                            while True:
                                try:
                                    path = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.",
                                                                   delete_after=5)

                                else:
                                    if path.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                       delete_after=5)

                                    try:
                                        get_item = recurse_index(
                                            self.bot.user_data["Directories"][reaction.message.guild.id]['tree'],
                                            path.content.split("//"))

                                        if isinstance(get_item, int):
                                            raise KeyError(str(path[-1]))

                                    except KeyError as e:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Enter the path where channel "
                                                    f"you want to hide is located:\n"
                                                    f"Path: \\_\\_\\_\\_\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: That directory doesn't exist. "
                                                    f"Level `{e}` is not found.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue
                                    else:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name of the target channel:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        break

                            while True:
                                try:
                                    name = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.",
                                                                   delete_after=5)
                                else:
                                    if name.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.",
                                                                       delete_after=5)

                                    get_item = recurse_index(
                                        self.bot.user_data["Directories"][reaction.message.guild.id]['tree'],
                                        path.content.split("//"))

                                    if name.content not in get_item:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name of the target channel:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: A category/channel with that name already exists.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue

                                    if len(name.content) > 50:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name of the target channel:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: Your name cannot exceed 50 characters in length.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue

                                    else:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"Done! One moment...\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: __{name.content}__\n"
                                        )
                                        await sleep(2)
                                        await confirmation.edit(content="Hiding channel...")
                                        ctx = await self.bot.get_context(reaction.message)
                                        await self.bot.get_command("hide_channel").callback(self, ctx,
                                                                                            path.content,
                                                                                            name.content
                                                                                            )
                                        await confirmation.delete()
                                        break

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user = self.bot.get_user(payload.user_id)

        ctx = await self.bot.get_context(message)

        if user == self.bot.user:
            return

        if ctx.guild and ctx.guild.id in self.bot.user_data["Directories"]:
            if ctx.message.id == self.bot.user_data["Directories"][ctx.guild.id]["messageID"]:
                if str(payload.emoji) == "🔄" and payload.user_id != self.bot.user.id:

                    # Check permissions for the user and bot
                    perms = user.permissions_in(ctx.channel)
                    if not perms.manage_channels:
                        await ctx.channel.send(
                            f"**{user}**, you require the \"Manage Channels\" permission in this channel to use this.",
                            delete_after=5)
                        return

                    dcategory = self.bot.get_channel(self.bot.user_data["Directories"][ctx.guild.id]["categoryID"])
                    bot_perms = ctx.guild.me.permissions_in(dcategory)

                    if not bot_perms.manage_channels:
                        await user.send("I can't update the directory because I don't have the `Manage Channels` permission!\n"
                                        "If you would, please remove your reaction and keep the channel clean...")
                        return

                    if ctx.guild.id in self.bot.using_gui:
                        if self.bot.using_gui[ctx.guild.id] == user.id:
                            await ctx.channel.send(
                                f"**{user}**, please answer the prompt first!",
                                delete_after=5
                            )
                            return
                        else:
                            user_inuse = self.bot.get_user(self.bot.using_gui[ctx.guild.id])
                            await ctx.channel.send(
                                f"{user.mention}, **{user_inuse}** is currently using the GUI.",
                                delete_after=5
                            )
                            return

                    else:
                        await self.bot.get_command("update").callback(self, ctx)

    # Errors
    @Cog.listener()
    async def on_command_error(self, ctx: Context, error: Exception):
        with suppress(Forbidden):
            await ctx.message.add_reaction("❌")

        if not isinstance(error, CommandOnCooldown):
            ctx.command.reset_cooldown(ctx)

        if not self.bot.config["debug_mode"]:
            msg = ctx.message
            if isinstance(error, BotMissingPermissions):
                if ctx.command.name == "setup_directory":
                    await ctx.author.send(
                        f"Every command requires the `Read Text Channels/Messages`, "
                        f"`Send Messages` and `Manage Messages` permissions.\n"
                        f"The `setup_directory` command also requires following permissions:\n"
                        f"```\n"
                        f"Manage Channels - To create your new channel system. "
                        f"This will not erase any outside channels.\n"
                        f"Add Reactions - To add buttons to make it more convenient to answer confirmation messages.\n"
                        f"Manage Roles - To change the permissions "
                        f"in the \"directory\" channel so only you and the server owner "
                        f"(if you're not a higher role than me*) can edit until further permissions are set.\n"
                        f"```"
                        f"\\*Consult moderators if you don't have permission to use the directory channel created."
                    )

                elif ctx.command.name == "teardown_directory":
                    await ctx.author.send(
                        f"Every command requires the `Read Text Channels/Messages`, "
                        f"`Send Messages` and `Manage Messages` permissions.\n"
                        f"The `teardown_directory` command also requires following permissions:\n"
                        f"```\n"
                        f"Manage Channels - To delete channels under the managed category. "
                        f"This does not delete channels outside said category UNLESS a category ID is provided.\n"
                        f"```"
                    )

                elif ctx.command.name == "create_channel":
                    await ctx.author.send(
                        f"Every command requires the `Read Text Channels/Messages`, "
                        f"`Send Messages` and `Manage Messages` permissions.\n"
                        f"The `create_channel` command also requires following permissions:\n"
                        f"```\n"
                        f"Manage Channels - To create new channels using the new channel system.\n"
                        f"```"
                    )

                elif ctx.command.name == "create_category":
                    await ctx.author.send(
                        f"Every command requires the `Read Text Channels/Messages`, "
                        f"`Send Messages` and `Manage Messages` permissions.\n"
                        f"The `create_category` command requires no additional permissions."
                    )

                elif ctx.command.name == "delete_category":
                    await ctx.author.send(
                        f"Every command requires the `Read Text Channels/Messages`, "
                        f"`Send Messages` and `Manage Messages` permissions.\n"
                        f"The `delete_category` command also requires following permissions:\n"
                        f"```\n"
                        f"Manage Channels - To delete channels under a V2* category.\n"
                        f"```\n"
                        f"\\* A V2 category is a category created by me, and is not associated with Discord. "
                        f"It is involved with the new system."
                    )

                elif ctx.command.name == "rename_channel":
                    await ctx.author.send(
                        f"Every command requires the `Read Text Channels/Messages`, "
                        f"`Send Messages` and `Manage Messages` permissions.\n"
                        f"The `rename_channel` command also requires following permissions:\n"
                        f"```\n"
                        f"Manage Channels - To rename channels created with the new system.\n"
                        f"```\n"
                        f"This command can also rename V2\\* categories.\n"
                        f"\\* A V2 category is a category created by me, and is not associated with Discord."
                    )

                elif ctx.command.name == "move_channel":
                    await ctx.author.send(
                        f"Every command requires the `Read Text Channels/Messages`, "
                        f"`Send Messages` and `Manage Messages` permissions.\n"
                        f"The `move_channel` command requires no additional permissions."
                    )

                elif ctx.command.name == "import_channel":
                    await ctx.author.send(
                        f"Every command requires the `Read Text Channels/Messages`, "
                        f"`Send Messages` and `Manage Messages` permissions.\n"
                        f"The `import_channel` command requires no additional permissions."
                    )

                elif ctx.command.name == "hide_channel":
                    await ctx.author.send(
                        f"Every command requires the `Read Text Channels/Messages`, "
                        f"`Send Messages` and `Manage Messages` permissions.\n"
                        f"The `hide_channel` command requires no additional permissions."
                    )

                elif ctx.command.name == "save_directory":
                    await ctx.author.send(
                        f"Every command requires the `Read Text Channels/Messages`, "
                        f"`Send Messages` and `Manage Messages` permissions.\n"
                        f"The `save_directory` command requires no additional permissions."
                    )

                elif ctx.command.name == "preview_directory":
                    await ctx.author.send(
                        f"Every command requires the `Read Text Channels/Messages`, "
                        f"`Send Messages` and `Manage Messages` permissions.\n"
                        f"The `preview_directory` command requires no additional permissions."
                    )

                return

            elif isinstance(error, NotOwner):
                with suppress(Forbidden):
                    await ctx.message.add_reaction("❌")

                await msg.author.send(
                    "That command is not listed in the help menu and is to be used by the owner only."
                )
                return

            elif isinstance(error, MissingRequiredArgument):
                with suppress(Forbidden):
                    await ctx.message.add_reaction("❌")

                await msg.author.send(f"\"{error.param.name}\" is a required argument that is missing.")
                return

            elif isinstance(error, CommandNotFound):
                with suppress(Forbidden):
                    await ctx.message.add_reaction("❌")

                supposed_command = msg.content.split()[0]
                await msg.author.send(f"Command \"{supposed_command}\" doesn't exist.")
                return

            elif isinstance(error, MissingPermissions):
                with suppress(Forbidden):
                    await ctx.message.add_reaction("❌")

                await msg.author.send(
                    f"You require the Manage Channels and Manage Server permissions to create and "
                    f"teardown the directory, and to make new channels."
                )
                return

            elif isinstance(error, CommandOnCooldown):
                with suppress(Forbidden):
                    await ctx.message.add_reaction("❌")

                await msg.author.send(
                    f"That command is on a {round(error.cooldown.per)} second cooldown.\n"
                    f"Retry in {round(error.retry_after)} seconds."
                )

            else:
                if ctx.command.name is not None:
                    await ctx.author.send(
                        f"[Error in command \"{ctx.command.name}\"] {error}\n"
                        f"If you keep getting this error, let the developer know!\n"
                        f"In the case of a `404 Not Found` error, try using the "
                        f"`{self.bot.command_prefix}update` command."
                    )
                    print(f"[Error in command \"{ctx.command.name}\"]", str(error))

                else:
                    await ctx.author.send(
                        f"[Error outside of command] {error}\n"
                        f"If you keep getting this error, let the developer know!"
                    )
                    print("[Error outside of command]", error)

        else:
            raise error


def setup(bot: Bot):
    bot.add_cog(Events(bot))
