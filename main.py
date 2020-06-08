# https://discord.com/oauth2/authorize?client_id=698965636432265227&permissions=268479504&scope=bot

# Lib
from pickle import dump

# Site
from discord import __version__
from discord.activity import Activity
from discord.enums import ActivityType, Status
from discord.errors import LoginFailure
from discord.permissions import Permissions
from discord.utils import oauth_url

# Local
from utils.classes import Bot


debug_mode = input("Enter debug mode? (D=accept)\n---| ")
if debug_mode == "D":
    debug_mode = True

while True:
    tz = input("Time Zone:\n---| ")
    if tz in ["EST", "CST"]:
        break


print("Loading...")


BOT_PREFIX = "cdr:"
INIT_EXTENSIONS = [
    "admin",
    "background",
    "directory_management",
    "events",
    "help"
]


bot = Bot(
    command_prefix=BOT_PREFIX,
    description="CCreate a custom directory to better organize your channels.",
    owner_id=331551368789622784,
    debug_mode=debug_mode,
    tz=tz
)

bot.remove_command("help")


print(f"Running in: {bot.cwd}")
print(f"Discord API version: {__version__}")




@bot.event
async def on_ready():

    app_info = await bot.application_info()
    bot.owner = bot.get_user(app_info.owner.id)

    permissions = Permissions()
    permissions.update(
        manage_roles=True,
        manage_channels=True,
        manage_messages=True,
        read_messages=True,
        send_messages=True,
        attach_files=True
    )

    await bot.change_presence(status=Status.idle, activity=Activity(type=ActivityType.listening, name="Just woke up."))
    # check changelog for differences since last save
    with open(f"{bot.cwd}\\changelog.txt", "r") as clfp:
        content = clfp.read()
        if content != bot.univ.ChangelogCache:
            for guild in bot.guilds:
                if guild.system_channel:
                    try:
                        await guild.system_channel.send(f"Changelog updated:\n```{content} ​```")
                    except Exception:
                        pass

            bot.univ.ChangelogCache = content
            with open(f"{bot.cwd}\\Serialized\\data.pkl", "wb") as pkfp:
                try:
                    data = {
                        "VanityAvatars": bot.univ.VanityAvatars,
                        "Blacklists": bot.univ.Blacklists,
                        "Closets": bot.univ.Closets,
                        "ServerBlacklists": bot.univ.ServerBlacklists,
                        "ChangelogCache": bot.univ.ChangelogCache
                    }

                    dump(data, pkfp)
                except Exception:
                    pass

            print("[] Sent changelog updates.")

    print(f"\n"
          f"#-------------------------------#"
          f"| Loading initial cogs..."
          f"#-------------------------------#")

    for cog in INIT_EXTENSIONS:
        print(f"| Loading initial cog {cog}")
        try:
            bot.load_extension(f"cogs.{cog}")
        except Exception as e:
            print(f"| Failed to load extension {cog}\n|   {type(e).__name__}: {e}")

    print(f"#-------------------------------#\n"
          f"| Successfully logged in.\n"
          f"#-------------------------------#\n"
          f"| Usern:     {bot.user}\n"
          f"| User ID:   {bot.user.id}\n"
          f"| Owner:     {bot.owner}\n"
          f"| Guilds:    {len(bot.guilds)}\n"
          f"| Users:     {len(list(bot.get_all_members()))}\n"
          f"| OAuth URL: {oauth_url(app_info.id, permissions)}\n"
          f"# ------------------------------#")


if __name__ == "__main__":

    if not bot.auth.MWS_DBL_SUCCESS:
        if bot.auth.MWS_DBL_TOKEN:
            confirm_new_dbl_token = input("Last DBL login failed or unknown. Enter new token? (Y/n): ")
            confirm_new_dbl_token = confirm_new_dbl_token.lower().startswith("y")

        else:
            print("No DBL token stored.", end="")
            confirm_new_dbl_token = True
            
        if confirm_new_dbl_token:
            new_bdl_token = input("Enter new DBL token:\n")
            bot.auth.MWS_DBL_SUCCESS = new_bdl_token

    print("Logging in with token.")

    while True:

        try:

            if not bot.auth.MWS_BOT_TOKEN:
                raise LoginFailure

            bot.run()

        except LoginFailure:
            try:
                bot.auth.MWS_BOT_TOKEN = None

                print("\nLogin Failed: No token was provided or token provided was invalid.")
                new_token = input("Provide new bot token: ")

                bot.auth.MWS_BOT_TOKEN = new_token

            except KeyboardInterrupt:
                print("\nLogin with new bot token cancelled. Aborting.")
                break

        except KeyboardInterrupt:
            break

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
