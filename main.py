# https://discord.com/oauth2/authorize?client_id=698965636432265227&permissions=268479504&scope=bot
global TimeZone
global debug_mode
debug_mode = input("Enter debug mode? (D=accept)\n---| ")
while True:
    TimeZone = input("Time Zone:\n---| ")
    if TimeZone in ["EST", "CST"]:
        break

print("Loading...")

#Lib
import os
import pickle

#Site
import discord
from discord.ext.commands import Bot


Dir1 = os.getcwd()
print("Running in: "+Dir1)
print("Discord API version: " + discord.__version__)

# Main Initialize
#--------------------------------------------------------------
BOT_PREFIX = "cdr:"
BOT_TOKEN = '##'

bot = Bot(
    command_prefix=BOT_PREFIX,
    description="Create a new channel directory system in your servers.",
    owner_id=331551368789622784
)

if not os.path.exists(f"{Dir1}\\Serialized\\data.pkl"):
    print("[Unable to save] data.pkl not found. Replace file before shutting down. Saving disabled.")
    univ.DisableSaving = True
    univ.Directories = {"guildID":{"catagoryID":0, "channelID":0, "msgID":0, "tree":{}}}

else:
    univ.DisableSaving = False
    with open(f"{Dir1}\\Serialized\\data.pkl", "rb") as f:
        try:
            data = pickle.Unpickler(f).load()
            univ.Directories = data["Directories"]
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



# Run
#--------------------------------------------------------------

bot.run(BOT_TOKEN)

#--------------------------------------------------------------
