# Lib
from os.path import exists
from picke import dump

# Site
from discord.ext import commands
from discord.ext.commands.cog import Cog

# Local
from utils.classes import Bot

class admin(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="logout")
    @commands.is_owner()
    async def blogout(self, ctx):
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
    bot.add_cog(admin)