
# Lib
from asyncio import sleep
from asyncio.exceptions import TimeoutError
from contextlib import suppress
from copy import deepcopy

# Site
from discord import Reaction, User
from discord.channel import CategoryChannel
from discord.ext.commands.context import Context
from discord.ext.commands.cog import Cog
from discord.ext.commands.errors import (
    BotMissingPermissions,
    MissingPermissions,
    CommandNotFound,
    MissingRequiredArgument,
    NotOwner,
    CommandOnCooldown
)
from discord.errors import Forbidden

# Local
from utils.classes import Bot
from utils.directory_mgmt import loadingupdate as lucm, recurse_index, usinggui

class Events(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if channel.guild.id not in self.bot.univ.LoadingUpdate and channel.guild.id in self.bot.univ.Directories:
            with lucm(self.bot, channel.guild.id):
                await sleep(5)
                catch_id = deepcopy(self.bot.univ.Directories[channel.guild.id]["categoryID"])
                await self.bot.update_directory(channel,
                                                note="Updated automatically following channel deletion by user.")
                if isinstance(channel, CategoryChannel) and channel.id == catch_id:
                    async def recurse_move_channels(d: dict):
                        for key, val in d.items():
                            if isinstance(val, tuple):
                                ch = self.bot.get_channel(val[0])
                                dcategory = self.bot.get_channel(
                                    self.bot.univ.Directories[channel.guild.id]["categoryID"])
                                if ch and not val[1]:
                                    await ch.edit(category=dcategory)
                            elif isinstance(val, dict):
                                await recurse_move_channels(d[key])
                            else:
                                raise ValueError("Invalid directory dictionary passed.")

                    await recurse_move_channels(self.bot.univ.Directories[channel.guild.id]["tree"])

    @Cog.listener()
    async def on_message(self, msg):
        if not msg.guild:
            return

        if msg.author.id == self.bot.user.id:
            return

        verify_command = await self.bot.get_context(msg)
        if verify_command.valid:
            self.bot.univ.Inactive = 0
            return

        if msg.guild.id in self.bot.univ.Directories:
            if msg.channel.id == self.bot.univ.Directories[msg.guild.id]["channelID"]:
                try:
                    await msg.delete()
                except Forbidden:
                    pass

        if self.bot.user.mentioned_in(msg):
            try:
                if msg.author.id in self.bot.owner_ids:
                    await msg.add_reaction("💕")
                else:
                    await msg.add_reaction("👋")
            except Forbidden:
                pass

    @Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, user: User):
        if reaction.message.guild and reaction.message.guild.id in self.bot.univ.Directories:
            if reaction.message.id == self.bot.univ.Directories[reaction.message.guild.id]["messageID"]:
                if reaction.message.guild.id in self.bot.univ.pause_reaction_listening:
                    return

                if user == self.bot.user:
                    return
                else:
                    await reaction.remove(user)

                if reaction.message.guild.id in self.bot.univ.using_gui:
                    if self.bot.univ.using_gui[reaction.message.guild.id] == user.id:
                        await reaction.message.channel.send(
                            f"**{user}**, please answer the prompt first!",
                            delete_after=5
                        )
                        return
                    else:
                        user_inuse = self.bot.get_user(self.bot.univ.using_gui[reaction.message.guild.id])
                        await reaction.message.channel.send(
                            f"{user.mention}, **{user_inuse}** is currently using the GUI.",
                            delete_after=5
                        )
                        return

                with usinggui(self.bot, reaction.message.guild.id, user.id):
                    if str(reaction.emoji) == "📝":
                        await reaction.message.clear_reactions()

                        info = await reaction.message.channel.send(
                            f"**{user}**, The above buttons are **guided** commands.\n"
                            f"To cancel, simply wait about 10 seconds."
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
                        await reaction.message.add_reaction("1️⃣")
                        await reaction.message.add_reaction("2️⃣")
                        await reaction.message.add_reaction("3️⃣")
                        await reaction.message.add_reaction("4️⃣")
                        await reaction.message.add_reaction("5️⃣")
                        await reaction.message.add_reaction("6️⃣")
                        await reaction.message.add_reaction("7️⃣")
                    else:
                        return

                    def check(rreaction, uuser):
                        return str(rreaction.emoji) in ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"] and rreaction.message == reaction.message and uuser == user

                    self.bot.univ.pause_reaction_listening.append(reaction.message.guild.id)
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=15, check=check)
                    except TimeoutError:
                        self.bot.univ.pause_reaction_listening.remove(reaction.message.guild.id)
                        await reaction.message.clear_reactions()
                        await info.edit(content=f":x: **{user}** timed out.", delete_after=5)
                        await reaction.message.add_reaction("📝")
                        await reaction.message.add_reaction("🔄")

                    else:
                        self.bot.univ.pause_reaction_listening.remove(reaction.message.guild.id)
                        await reaction.message.clear_reactions()
                        await info.delete()

                        if str(reaction.emoji) == "1️⃣":
                            confirmation = await reaction.message.channel.send(
                                f"**{user}**\n"
                                f"[60 seconds] Enter the path where you would like to create this channel:\n"
                                f"Path: \\_\\_\\_\\_\n"
                                f"Name: \\_\\_\\_\\_\n"
                                f"Type \"+Cancel\" to cancel.")

                            def check(msg):
                                return msg.author == user and msg.channel == reaction.message.channel

                            while True:
                                try:
                                    path = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.", delete_after=5)

                                else:
                                    if path.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)

                                    try:
                                        get_item = recurse_index(
                                            self.bot.univ.Directories[reaction.message.guild.id]['tree'],
                                            path.content.split("//"))

                                        if isinstance(get_item, int):
                                            raise KeyError(str(path[-1]))

                                    except KeyError as e:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Enter the path where you would like to create this channel:\n"
                                                    f"Path: \\_\\_\\_\\_\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: That directory doesn't exist. Level `{e}` is not found.\n"
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

                            def check(msg):
                                return msg.author == user and msg.channel == reaction.message.channel

                            while True:
                                try:
                                    name = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.", delete_after=5)
                                else:
                                    if name.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)

                                    get_item = recurse_index(
                                        self.bot.univ.Directories[reaction.message.guild.id]['tree'],
                                        path.content.split("//"))

                                    if isinstance(get_item, dict) and name.content in get_item:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name of your new channel:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: A category/channel with that name already exists in that directory.\n"
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
                                        await self.bot.get_command("create_channel").callback(self, ctx, path.content, name.content)
                                        await confirmation.delete()
                                        break

                        elif str(reaction.emoji) == "2️⃣":
                            confirmation = await reaction.message.channel.send(
                                f"**{user}**\n"
                                f"[60 seconds] Enter the path where you would like to create this category:\n"
                                f"Path: \\_\\_\\_\\_\n"
                                f"Name: \\_\\_\\_\\_\n"
                                f"Type \"+Cancel\" to cancel.")

                            def check(msg):
                                return msg.author == user and msg.channel == reaction.message.channel

                            while True:
                                try:
                                    path = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.", delete_after=5)
                                else:
                                    if path.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)

                                    try:
                                        get_item = recurse_index(
                                            self.bot.univ.Directories[reaction.message.guild.id]['tree'],
                                            path.content.split("//"))

                                        if isinstance(get_item, int):
                                            raise KeyError(str(path[-1]))

                                    except KeyError as e:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Enter the path where you would like to create this category:\n "
                                                    f"Path: \\_\\_\\_\\_\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: That directory doesn't exist. Level `{e}` is not found.\n"
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

                            def check(msg):
                                return msg.author == user and msg.channel == reaction.message.channel

                            while True:
                                try:
                                    name = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.")
                                else:
                                    if name.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)

                                    get_item = recurse_index(
                                        self.bot.univ.Directories[reaction.message.guild.id]['tree'],
                                        path.content.split("//"))

                                    if name.content in get_item:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name of your new category:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: A category/channel with that name already exists in that directory.\n"
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
                                        await self.bot.get_command("create_category").callback(self, ctx, path.content, name.content)
                                        await confirmation.delete()
                                        break

                        elif str(reaction.emoji) == "3️⃣":
                            confirmation = await reaction.message.channel.send(
                                f"**{user}**\n"
                                f"[60 seconds] Enter the path where you would like to delete a category:\n"
                                f"Path: \\_\\_\\_\\_\n"
                                f"Name: \\_\\_\\_\\_\n"
                                f"Type \"+Cancel\" to cancel.")

                            def check(msg):
                                return msg.author == user and msg.channel == reaction.message.channel

                            while True:
                                try:
                                    path = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)
                                else:
                                    if path.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)

                                    try:
                                        get_item = recurse_index(
                                            self.bot.univ.Directories[reaction.message.guild.id]['tree'],
                                            path.content.split("//"))

                                        if isinstance(get_item, int):
                                            raise KeyError(str(path[-1]))

                                    except KeyError as e:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Enter the path where you would like to delete a category:\n "
                                                    f"Path: \\_\\_\\_\\_\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: That directory doesn't exist. Level `{e}` is not found.\n"
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

                            def check(msg):
                                return msg.author == user and msg.channel == reaction.message.channel

                            while True:
                                try:
                                    name = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.", delete_after=5)
                                else:
                                    if name.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)

                                    get_item = recurse_index(
                                        self.bot.univ.Directories[reaction.message.guild.id]['tree'],
                                        path.content.split("//"))

                                    if isinstance(get_item, dict) and name.content not in get_item:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name of the target category:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: A category with that name doesn't exist in that directory.\n"
                                                    f"Type \"+Cancel\" to cancel.")
                                        continue

                                    elif isinstance(get_item, tuple):
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the name of the target category:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: That's a channel, not a category. Navigate to the channel and delete it manually.\n"
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
                                        await self.bot.get_command("delete_category").callback(self, ctx, path.content, name.content)
                                        await confirmation.delete()
                                        break

                        elif str(reaction.emoji) == "4️⃣":
                            confirmation = await reaction.message.channel.send(
                                f"**{user}**\n"
                                f"[60 seconds] Enter the path where you would like to rename a category or channel:\n"
                                f"Path: \\_\\_\\_\\_\n"
                                f"Name: \\_\\_\\_\\_\n"
                                f"Rename: \\_\\_\\_\\_\n"
                                f"Type \"+Cancel\" to cancel.")

                            def check(msg):
                                return msg.author == user and msg.channel == reaction.message.channel

                            while True:
                                try:
                                    path = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.", delete_after=5)
                                else:
                                    if path.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)

                                    try:
                                        get_item = recurse_index(
                                            self.bot.univ.Directories[reaction.message.guild.id]['tree'],
                                            path.content.split("//"))

                                        if isinstance(get_item, int):
                                            raise KeyError(str(path[-1]))

                                    except KeyError as e:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Enter the path where you would like to rename a category or channel:\n "
                                                    f"Path: \\_\\_\\_\\_\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f"Rename: \\_\\_\\_\\_\n"
                                                    f":warning: That directory doesn't exist. Level `{e}` is not found.\n"
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

                            def check(msg):
                                return msg.author == user and msg.channel == reaction.message.channel

                            while True:
                                try:
                                    name = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.", delete_after=5)
                                else:
                                    if name.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)

                                    get_item = recurse_index(
                                        self.bot.univ.Directories[reaction.message.guild.id]['tree'],
                                        path.content.split("//"))

                                    if name.content not in get_item:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the the target's name:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f"Rename: \\_\\_\\_\\_\n"
                                                    f":warning: A category/channel with that name doesn't exist in that directory.\n"
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

                            def check_rename(msg):
                                return msg.author == user and msg.channel == reaction.message.channel

                            while True:
                                try:
                                    rename = await self.bot.wait_for("message", timeout=60, check=check_rename)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)
                                else:
                                    if rename.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)

                                    get_item = recurse_index(
                                        self.bot.univ.Directories[reaction.message.guild.id]['tree'],
                                        path.content.split("//"))

                                    if rename.content in get_item:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the the target's **new** name:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: __{name.content}__\n"
                                                    f"Rename: \\_\\_\\_\\_\n"
                                                    f":warning: A category/channel with that name already exists in that directory.\n"
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
                                        await self.bot.get_command("rename_channel").callback(self, ctx, path.content, name.content, rename.content)
                                        await confirmation.delete()
                                        break

                        elif str(reaction.emoji) == "5️⃣":
                            confirmation = await reaction.message.channel.send(
                                f"**{user}**\n"
                                f"[60 seconds] Enter the path where you would like to move a category or channel:\n"
                                f"Path: \\_\\_\\_\\_\n"
                                f"Name: \\_\\_\\_\\_\n"
                                f"New Path: \\_\\_\\_\\_\n"
                                f"Type \"+Cancel\" to cancel.")

                            def check(msg):
                                return msg.author == user and msg.channel == reaction.message.channel

                            while True:
                                try:
                                    path = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.", delete_after=5)
                                else:
                                    if path.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)

                                    try:
                                        get_item = recurse_index(
                                            self.bot.univ.Directories[reaction.message.guild.id]['tree'],
                                            path.content.split("//"))

                                        if isinstance(get_item, int):
                                            raise KeyError(str(path[-1]))

                                    except KeyError as e:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Enter the path where you would like to move a category or channel:\n "
                                                    f"Path: \\_\\_\\_\\_\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f"New Path: \\_\\_\\_\\_\n"
                                                    f":warning: That directory doesn't exist. Level `{e}` is not found.\n"
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

                            def check(msg):
                                return msg.author == user and msg.channel == reaction.message.channel

                            while True:
                                try:
                                    name = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.", delete_after=5)
                                else:
                                    if name.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)

                                    get_item = recurse_index(
                                        self.bot.univ.Directories[reaction.message.guild.id]['tree'],
                                        path.content.split("//"))

                                    if name.content not in get_item:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the the target's name:\n"
                                                    f"Path: __{path.content}__\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f"New Path: \\_\\_\\_\\_\n"
                                                    f":warning: A category/channel with that name doesn't exist in that directory.\n"
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

                            def check(msg):
                                return msg.author == user and msg.channel == reaction.message.channel

                            while True:
                                try:
                                    new_path = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)
                                else:
                                    if new_path.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)

                                    try:
                                        get_new_item = recurse_index(
                                            self.bot.univ.Directories[reaction.message.guild.id]['tree'],
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
                                                    f":warning: Your destination path doesn't exist. Level `{e}` is not found.\n"
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
                                                        f":warning: A category/channel already has the same name as your target. Rename either channel and try again.\n"
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
                                            await self.bot.get_command("move_channel").callback(self, ctx, path.content, name.content, new_path.content)
                                            await confirmation.delete()
                                            break

                        elif str(reaction.emoji) == "6️⃣":
                            confirmation = await reaction.message.channel.send(
                                f"**{user}**\n"
                                f"[60 seconds] Mention the channel you would like to import:\n"
                                f"Channel: \\_\\_\\_\\_\n"
                                f"Path: \\_\\_\\_\\_\n"
                                f"Name: \\_\\_\\_\\_\n"
                                f"Type \"+Cancel\" to cancel.")

                            def check(msg):
                                return msg.author == user and msg.channel == reaction.message.channel

                            while True:
                                try:
                                    channel = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.", delete_after=5)
                                else:
                                    if channel.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)

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

                                    tree = deepcopy(self.bot.univ.Directories[reaction.message.guild.id]["tree"])
                                    while True:
                                        ids = self.bot.get_all_ids(tree, c_ids=list())
                                        if isinstance(ids, dict):
                                            tree = ids
                                            continue
                                        elif isinstance(ids, list):
                                            break

                                    if isinstance(ids, list):
                                        if channel_found.id in ids:
                                            await confirmation.edit(
                                                content=f"**{user}**\n"
                                                        f"[60 seconds] Now, enter the name to import this channel as:\n"
                                                        f"Channal: \\_\\_\\_\\_\n"
                                                        f"Path: \\_\\_\\_\\_\n"
                                                        f"Name: \\_\\_\\_\\_\n"
                                                        f":warning: That channel is already in the directory. "
                                                        f"It was either created with the new system, or already imported.\n"
                                                        f"Type \"+Cancel\" to cancel.")
                                            continue

                                    await confirmation.edit(
                                        content=f"**{user}**\n"
                                                f"[60 seconds] Now, enter the path you would like to import this channel into:\n"
                                                f"Channel: __{channel_found.mention}__\n"
                                                f"Path: \\_\\_\\_\\_\n"
                                                f"Name: \\_\\_\\_\\_\n"
                                                f"Type \"+Cancel\" to cancel.")
                                    break

                            def check(msg):
                                return msg.author == user and msg.channel == reaction.message.channel

                            while True:
                                try:
                                    path = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.", delete_after=5)
                                else:
                                    if path.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)

                                    try:
                                        get_item = recurse_index(
                                            self.bot.univ.Directories[reaction.message.guild.id]['tree'],
                                            path.content.split("//"))
                                    except KeyError as e:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Now, enter the path you would like to import this channel into:\n"
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

                            def check(msg):
                                return msg.author == user and msg.channel == reaction.message.channel

                            while True:
                                try:
                                    name = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)
                                else:
                                    if name.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)

                                    get_item = recurse_index(
                                        self.bot.univ.Directories[reaction.message.guild.id]['tree'],
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
                                        await self.bot.get_command("import_channel").callback(self, ctx, channel_found, path.content, name.content)
                                        await confirmation.delete()
                                        break

                        elif str(reaction.emoji) == "7️⃣":
                            confirmation = await reaction.message.channel.send(
                                f"**{user}**\n"
                                f"[60 seconds] Enter the path where channel you want to hide is located:\n"
                                f"Path: \\_\\_\\_\\_\n"
                                f"Name: \\_\\_\\_\\_\n"
                                f"Type \"+Cancel\" to cancel.")

                            def check(msg):
                                return msg.author == user and msg.channel == reaction.message.channel

                            while True:
                                try:
                                    path = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.", delete_after=5)

                                else:
                                    if path.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)

                                    try:
                                        get_item = recurse_index(
                                            self.bot.univ.Directories[reaction.message.guild.id]['tree'],
                                            path.content.split("//"))

                                        if isinstance(get_item, int):
                                            raise KeyError(str(path[-1]))

                                    except KeyError as e:
                                        await confirmation.edit(
                                            content=f"**{user}**\n"
                                                    f"[60 seconds] Enter the path where channel you want to hide is located:\n"
                                                    f"Path: \\_\\_\\_\\_\n"
                                                    f"Name: \\_\\_\\_\\_\n"
                                                    f":warning: That directory doesn't exist. Level `{e}` is not found.\n"
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

                            def check(msg):
                                return msg.author == user and msg.channel == reaction.message.channel

                            while True:
                                try:
                                    name = await self.bot.wait_for("message", timeout=60, check=check)
                                except TimeoutError:
                                    await reaction.message.clear_reactions()
                                    await reaction.message.add_reaction("📝")
                                    await reaction.message.add_reaction("🔄")
                                    return await confirmation.edit(content=f":x: **{user}** timed out.", delete_after=5)
                                else:
                                    if name.content == "+Cancel":
                                        await reaction.message.clear_reactions()
                                        await reaction.message.add_reaction("📝")
                                        await reaction.message.add_reaction("🔄")
                                        return await confirmation.edit(content=f":x: **{user}** cancelled.", delete_after=5)

                                    get_item = recurse_index(
                                        self.bot.univ.Directories[reaction.message.guild.id]['tree'],
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
                                        await self.bot.get_command("hide_channel").callback(self, ctx, path.content, name.content)
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

        if ctx.guild and ctx.guild.id in self.bot.univ.Directories:
            if ctx.message.id == self.bot.univ.Directories[ctx.guild.id]["messageID"]:
                if str(payload.emoji) == "🔄" and payload.user_id != self.bot.user.id:

                    if ctx.guild.id in self.bot.univ.using_gui:
                        if self.bot.univ.using_gui[ctx.guild.id] == user.id:
                            await ctx.message.channel.send(
                                f"**{user}**, please answer the prompt first!",
                                delete_after=5
                            )
                            return
                        else:
                            user_inuse = self.bot.get_user(self.bot.univ.using_gui[ctx.guild.id])
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
        if not self.bot.debug_mode:
            msg = ctx.message
            if isinstance(error, BotMissingPermissions):
                with suppress(Forbidden):
                    await ctx.message.add_reaction("❌")

                if ctx.command.name == "setup_directory":
                    await ctx.author.send(
                        f"Every command requires the `Read Text channels` and `Send Messages` permissions.\n"
                        f"The `setup_directory` command also requires following permissions:\n"
                        f"```\n"
                        f"Manage Channels - To create your new channel system. "
                        f"This will not erase any outside channels.\n"
                        f"Add Reactions - To add buttons to make it more convenient to answer confirmation messages\n"
                        f"Manage Roles - To change the permissions "
                        f"in the \"directory\" channel so only you and the server owner "
                        f"(if you're not a higher role than me*) can edit until further permissions are set.\n"
                        f"```"
                        f"\\*Consult moderators if you don't have permission to use the directory channel created."
                    )

                elif ctx.command.name == "teardown_directory":
                    await ctx.author.send(
                        f"Every command requires the `Read Text channels` and `Send Messages` permissions.\n"
                        f"The `teardown_directory` command also requires following permissions:\n"
                        f"```\n"
                        f"Manage Channels - To delete channels under the managed category. "
                        f"This does not delete channels outside said category UNLESS a category ID is provided.\n"
                        f"```"
                    )

                elif ctx.command.name == "create_channel":
                    await ctx.author.send(
                        f"Every command requires the `Read Text channels` and `Send Messages` permissions.\n"
                        f"The `create_channel` command also requires following permissions:\n"
                        f"```\n"
                        f"Manage Channels - To create new channels using the new channel system.\n"
                        f"```"
                    )

                elif ctx.command.name == "create_category":
                    await ctx.author.send(
                        f"Every command requires the `Read Text channels` and `Send Messages` permissions.\n"
                        f"The `create_category` command requires no additional permissions."
                    )

                elif ctx.command.name == "delete_category":
                    await ctx.author.send(
                        f"Every command requires the `Read Text channels` and `Send Messages` permissions.\n"
                        f"The `delete_category` command also requires following permissions:\n"
                        f"```\n"
                        f"Manage Channels - To delete channels under a V2* category.\n"
                        f"```\n"
                        f"\\* A V2 category is a category created by me, and is not associated with Discord. "
                        f"It is involved with the new system."
                    )

                elif ctx.command.name == "rename_channel":
                    await ctx.author.send(
                        f"Every command requires the `Read Text channels` and `Send Messages` permissions.\n"
                        f"The `rename_channel` command also requires following permissions:\n"
                        f"```\n"
                        f"Manage Channels - To rename channels created with the new system.\n"
                        f"```\n"
                        f"This command can also rename V2\\* categories.\n"
                        f"\\* A V2 category is a category created by me, and is not associated with Discord."
                    )

                elif ctx.command.name == "move_channel":
                    await ctx.author.send(
                        f"Every command requires the `Read Text channels` and `Send Messages` permissions.\n"
                        f"The `move_channel` command requires no additional permissions."
                    )

                elif ctx.command.name == "import_channel":
                    await ctx.author.send(
                        f"Every command requires the `Read Text channels` and `Send Messages` permissions.\n"
                        f"The `import_channel` command requires no additional permissions."
                    )

                elif ctx.command.name == "hide_channel":
                    await ctx.author.send(
                        f"Every command requires the `Read Text channels` and `Send Messages` permissions.\n"
                        f"The `hide_channel` command requires no additional permissions."
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
