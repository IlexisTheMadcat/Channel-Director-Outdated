
# Lib
from os.path import exists
from pickle import dump

# Site
from discord.ext.commands.cog import Cog
from discord.ext.commands.context import Context
from discord.ext.commands.core import command, is_owner

# Local
from utils.classes import Bot


class Admin(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @command(name="logout")
    @is_owner()
    async def blogout(self, ctx: Context):
        await ctx.send("Logging out...")
        if not exists(f"{self.bot.cwd}\\Serialized\\data.pkl"):
            await ctx.send("[Unable to save] data.pkl not found. Replace file before shutting down.")
            print("[Unable to save] data.pkl not found. Replace file before shutting down.")
            return

        with open(f"{self.bot.cwd}\\Serialized\\data.pkl", "wb") as f:
            try:
                data = self.bot.univ.Directories
                dump(data, f)
            except Exception as e:
                await ctx.send("[Unable to save; Data Reset] Pickle dumping Error: "+ str(e))

        await self.bot.logout()


def setup(bot: Bot):
    bot.add_cog(Admin(bot))