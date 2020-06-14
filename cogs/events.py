
# Lib

# Site
from discord.channel import CategoryChannel
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


class Events(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if isinstance(channel, CategoryChannel):
            try:
                if channel.guild.id not in self.bot.univ.TearingDown and channel.id == self.bot.univ.Directories[channel.guild.id]["categoryID"]:
                    try:
                        directory = await self.bot.fetch_channel(self.bot.univ.Directories[channel.guild.id]["channelID"])
                    except NotFound:
                        return

                    try:
                        dmessage = await directory.fetch_message(self.bot.univ.Directories[channel.guild.id]["msgID"])
                    except NotFound:
                        await self.bot.update_directory(channel, note="Repaired directory message.")
                        
                    try: 
                        await dmessage.edit(content="All channels have been disorganized!")
                    except NotFound:
                        pass
                    
                    self.bot.univ.Directories.pop(channel.guild.id)

                    ch = channel.guild.system_channel
                    if ch:
                        await ch.send(f":anger: Awe, what a mess! Someone messed up my directory! Next time, PLEASE use the command `{self.bot.command_prefix}teardown` that I provided you to teardown the directories appropriately. Unfortunately I can't delete all the channels that have been disorganized!")
                else:
                    pass

            except KeyError or NotFound:
                pass

        if channel.guild.id in self.bot.univ.LoadingUpdate.keys() and channel.guild.id not in self.bot.univ.TearingDown:
            if not self.bot.univ.LoadingUpdate[channel.guild.id]:
                self.bot.univ.LoadingUpdate[channel.guild.id] = True
                try:
                    dchannel = await self.bot.fetch_channel(self.bot.univ.Directories[channel.guild.id]["channelID"])
                except NotFound:
                    pass
                else:
                    async with dchannel.typing():
                        await self.bot.update_directory(channel, note="Updated automatically following channel deletion by user.")
                    self.bot.univ.LoadingUpdate[channel.guild.id] = False

    @Cog.listener()
    async def on_ready(self):
        print("Logged in as", self.bot.user)
        print("ID:", self.bot.user.id)
        print('------')

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
        
        if msg.guild.id in self.bot.univ.Directories.keys():
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
                    f"`{self.bot.command_prefix}permissions`."
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
