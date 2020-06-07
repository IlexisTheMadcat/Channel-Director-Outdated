# Lib
from datetime import datetime
from os.path import exists
from pickle import dump

# Site
from discord.activity import Activity
from discord.enums import ActivityType, Status
from discord.ext.commands.cog import Cog
from discord.ext.tasks import loop

# Local
from utils.classes import Bot

class BackgroundTasks(Cog):
    """Background loops"""
    def __init__(self, bot):
        self.bot = bot
        # self.DBLtoken = "token"
        # self.dblpy = DBLClient(self.bot, self.DBLtoken, autopost=True)
        self.savetofile.start()
        self.status_change.start()

    @loop(seconds=60)
    async def status_change(self):
        utchour = str(datetime.now().hour)
        utcminute = str(datetime.now().minute)
        if len(utchour) == 1:
            utchour = "0" + utchour
        if len(utcminute) == 1:
            utcminute = "0" + utcminute
        utctime = f"{utchour}:{utcminute}"
        
        if self.bot.univ.Inactive >= 5:
            status = Status.idle
        else:
            status = Status.online

        MechHub = await self.bot.get_guild(504090302928125954)
        Ram = await MechHub.fetch_member(687427956364279873)
        if Ram.status == Status.offline:
            status = Status.dnd
            activity = Activity(type=ActivityType.watching, name="my sister sleep...")
        if self.bot.debug_mode == "D":
            activity = Activity(type=ActivityType.playing, name="in DEBUG MODE")
        if self.bot.univ.DisableSaving:
            activity = Activity(type=ActivityType.playing, name=f"with SAVING DISABLED")
        else:
            activity = Activity(type=ActivityType.watching, name=f"{self.bot.command_prefix}help | {self.bot.TimeZone}: {utctime}")
        
        await self.bot.change_presence(status=status, activity=activity)
    
    @loop(seconds=60)
    async def savetofile(self):
        hour = str(datetime.now().hour)
        minute = str(datetime.now().minute)
        date = str(str(datetime.now().date().month) + "/" + str(datetime.now().date().day) + "/" + str(datetime.now().date().year))
        if len(hour) == 1:
            hour = "0" + hour
        if len(minute) == 1:
            minute = "0" + minute
        time = f"{hour}:{minute}, {date}"

        if not exists(f"{self.bot.cwd}\\Serialized\\data.pkl") and not self.bot.univ.DisableSaving:
            self.bot.univ.DisableSaving = True
            print(f"[{time} || Unable to save] data.pkl not found. Replace file before shutting down. Saving disabled.")
            return

        elif exists(f"{self.bot.cwd}\\Serialized\\data.pkl") and self.bot.univ.DisableSaving:
            self.bot.univ.DisableSaving = False
            print(f"[{time}] Saving re-enabled.")
            return

        if self.bot.univ.DisableSaving == False:
            with open(f"{self.bot.cwd}\\Serialized\\data.pkl", "wb") as f:
                try:
                    dump(self.bot.univ.Directories, f)
                except Exception as e:
                    print(f"[{time} || Unable to save] Pickle dumping Error:", e)

            self.bot.univ.Inactive = self.bot.univ.Inactive+1
            print(f"[CDR: {time}] Saved data.")

def setup(bot: Bot):
    bot.add_cog(BackgroundTasks)