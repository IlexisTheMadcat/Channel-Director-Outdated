
# Lib

# Site
from asyncio import sleep
from contextlib import suppress

from discord.channel import CategoryChannel
from discord.ext.commands import cooldown
from discord.ext.commands.context import Context
from discord.ext.commands.cog import Cog
from discord.ext.commands.errors import (
    BotMissingPermissions, 
    MissingPermissions, 
    CommandNotFound, 
    MissingRequiredArgument, 
    NotOwner
)
from discord.errors import NotFound, Forbidden

# Local
from utils.classes import Bot
from utils.directory_mgmt import LoadingUpdate_contextmanager as lu_cm


class Events(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if channel.guild.id not in self.bot.univ.LoadingUpdate and channel.guild.id in self.bot.univ.Directories:
            with lu_cm(self.bot, channel.guild.id):
                await sleep(5)
                await self.bot.update_directory(channel, note="Updated automatically following channel deletion by user.")
                if isinstance(channel, CategoryChannel) and channel.id == self.bot.univ.Directories[channel.guild.id]["categoryID"]:
                    async def recurse_move_channels(d: dict):
                        for key, val in d.items():
                            if isinstance(val, tuple):
                                ch = self.bot.get_channel(val[0])
                                dcategory = self.bot.get_channel(self.bot.univ.Directories[channel.guild.id]["categoryID"])
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
                if msg.author.id == self.bot.owner_id:
                    await msg.add_reaction("💕")
                else:
                    await msg.add_reaction("👋")
            except Forbidden:
                pass

    # Errors
    @Cog.listener()
    async def on_command_error(self, ctx: Context, error: Exception):
        if not self.bot.debug_mode:
            msg = ctx.message
            if isinstance(error, BotMissingPermissions):
                await ctx.message.delete()
                await msg.author.send(
                    f"This bot is missing one or more permissions listed in "
                    f"`{self.bot.command_prefix}help` under `Required Permissions."
                )
                return

            elif isinstance(error, NotOwner):
                await ctx.message.delete()
                await msg.author.send(
                    "That command is not listed in the help menu and is to be used by the owner only."
                )
                return
            
            elif isinstance(error, MissingRequiredArgument):
                await ctx.message.delete()
                await msg.author.send(f"\"{error.param.name}\" is a required argument that is missing.")
                return
        
            elif isinstance(error, CommandNotFound):
                supposed_command = msg.content.split()[0]
                await ctx.message.delete()
                await msg.author.send(f"Command \"{supposed_command}\" doesn't exist.")
                return

            elif isinstance(error, MissingPermissions):
                await ctx.message.delete()
                await msg.author.send(
                    f"You require the Manage Channels and Manage Server permissions to create and "
                    f"teardown the directory, and to make new channels."
                )
                return
            
            else:
                if ctx.command.name is not None:
                    await ctx.author.send(
                        f"[Error in command \"{ctx.command.name}\"] {error}\nIf you keep getting this error, "
                        f"let the developer know!\nIn the case of a `404 Not Found` error, try using the "
                        f"`{self.bot.command_prefix}update` command."
                    )
                    print(f"[Error in command \"{ctx.command.name}\"]", str(error))

                else:
                    await ctx.author.send(
                        f"[Error outside of command] {error}\nIf you keep getting this error, let the developer know!"
                    )
                    print("[Error outside of command]", error)

        else:
            raise error


def setup(bot: Bot):
    bot.add_cog(Events(bot))
