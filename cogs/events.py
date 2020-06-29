
# Lib
from asyncio import sleep
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
from utils.directory_mgmt import LoadingUpdate_contextmanager as LuCm


class Events(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if channel.guild.id not in self.bot.univ.LoadingUpdate and channel.guild.id in self.bot.univ.Directories:
            with LuCm(self.bot, channel.guild.id):
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
            if reaction.message.id == self.bot.univ.Directories["messageID"]:
                await reaction.remove(user)
                if str(reaction.emoji) == "🔄":
                    pass

                elif reaction.emoji.id in self.bot.buttons:
                    pass

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
