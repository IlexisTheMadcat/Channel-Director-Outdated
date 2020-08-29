# Lib
from os import stat
from datetime import datetime

# Site
from os.path import exists

from discord import Embed, Permissions, AppInfo
from discord.ext.commands import Context, command, bot_has_permissions
from discord.ext.commands.cog import Cog
from discord.utils import oauth_url

# Local
from utils.classes import Bot


class MiscCommands(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command()
    @bot_has_permissions(send_messages=True)
    async def invite(self, ctx: Context):
        """Sends an OAuth bot invite URL"""

        app_info: AppInfo = await self.bot.application_info()
        permissions = Permissions()
        permissions.update(
            manage_channels=True,
            manage_roles=True,
            manage_messages=True,
            read_messages=True,
            send_messages=True,
            attach_files=True,
            add_reactions=True
        )

        em = Embed(
            title=f'OAuth URL for {self.bot.user.name}',
            description=f'[Click Here]'
                        f'({oauth_url(app_info.id, permissions)}) '
                        f'to invite me to your server.',
            color=0xaaeaff
        )
        await ctx.send(embed=em)

    @command(name="help")
    @bot_has_permissions(send_messages=True)
    async def bhelp(self, ctx, section="directory", subsection=None):
        BOT_PREFIX = self.bot.command_prefix
        em = Embed(title="Rem: Help", color=0xaaeaff)

        if section.lower() == "directory":
            em.description = f"""
New? Try these commands in your server:
```
{BOT_PREFIX}setup
{BOT_PREFIX}new_channel "root" "Front Yard"
{BOT_PREFIX}new_category "root" "Big House"
{BOT_PREFIX}new_channel "root//Big House" "Livingroom"
```
Required Permissions:
```
"Manage Roles"
To set the directory channel so that only the server owner may use it until further permissions are set.

"Manage Channels"
To create new channels.

"Manage Messages"
To manage the directory channel so that it's kept clean.

"Read Messages"
To read commands.

"Send Messages"
To send notifications/messages for warnings, confirmations, etc.

"Attach Files"
To send the requested file from the command {BOT_PREFIX}save_directory.

"Add Reactions"
To add buttons for your convenience while setting up or tearing down.
```
To see important announcements and command changes, Type and enter `{BOT_PREFIX}help updates`
Use this if you think a command isn't working the same way it did last time you used it.

--------------------------------------------------

Type `{BOT_PREFIX}help <directory>`, where `directory` is one of the following:
**Details**
**Commands**
**Updates**
"""

        elif section.lower() == "details":
            owners = [self.bot.get_user(uid).mention for uid in self.bot.owner_ids]
            owners = '\n'.join(owners)
            em.description = f"""
**Details:**
Command prefix: `{BOT_PREFIX}`
Create a custom directory to better organize your channels.

This bot was created by:
{owners}

Support Server invite: https://discord.gg/j2y7jxQ
Warning: Support server may contain swearing in open channels.
*Consider DMing the developer instead for questions/information.

Number of servers this bot is in now: {len(self.bot.guilds)}
:asterisk: Number of servers using the new directory system: {len(self.bot.user_data["Directories"])}
"""
        elif section.lower() == "updates":
            lastmodified = stat(f"{self.bot.cwd}/changelog.txt").st_mtime
            lastmodified = datetime.fromtimestamp(lastmodified).strftime("%H:%M %m/%d/%Y")
            if not exists(f"{self.bot.cwd}/changelog.txt"):
                open("{self.bot.cwd}/changelog.txt", "w").close()

            with open(f"{self.bot.cwd}/changelog.txt", "r") as f:
                text = f.read()

            if not text:
                text = "No new updates."

            em.description = f"""
**Updates**
__Here you will find important updates regarding command changes and announcements.__
```
Last updated: {lastmodified}
{text}
```
"""
            
        elif section.lower() == "commands":
            if subsection is None:
                em.description = f"""
**Commands**
Type `{BOT_PREFIX}help commands <command>`, where `command` is one of the following;
By each is the permission required to use it:
```
Directory management -- Control the directory setup
    setup           - "M/Server" and "M/Channels"
    teardown        - "M/Server" and "M/Channels"

Channel Management -- Manage channels in the directory
    create_channel    - "M/Channels"
    create_category   - "M/Channels"
    delete_category   - "M/Channels"
    rename_channel    - "M/Channels"
    move_channel      - "M/Channels"
    import_channel    - "M/Channels"
    hide_channel      - "M/Channels"
    update            - "M/Channels"
    save_directory    - No Limits
    preview_directory - No Limits

General -- General commands
    help   - No Limits
    invite - No Limits
```
"""
            elif subsection.lower() == "setup":
                em.description = f"""
**SETUP**; Aliases: "su"
`{BOT_PREFIX}setup`
------------------------------
Set up your new custom directory system.
**--** Attaching a cdr_directory.pkl file with proper contents generated by the `{BOT_PREFIX}save_directory` command will load an existing directory based on that file.
**--** You should never delete the category created by the bot. Doing this will disorganize potentially hundreds of channels under it.
**----** Do prevent these inconveniences that I should be worried about, use the `{BOT_PREFIX}teardown` command. I'll handle everything.
"""

            elif subsection.lower() == "teardown":
                em.description = f"""
**TEARDOWN**; Aliases: "td"
`{BOT_PREFIX}teardown`
------------------------------
Deconstruct the custom directory system added to your server, provided by me.
**--** IMPORTANT! Use this command especially if you have a lot of channels under the category that I created.
"""

            elif subsection.lower() == "new_channel":
                em.description = f"""
**CREATE_CHANNEL**; Aliases: "new_ch"
`{BOT_PREFIX}create_channel <directory> <name>`
------------------------------
Create a new channel under `directory` with the name `name`.
**--** It is recommended not to make 2 channels with the same name in the same directory! (This is not allowed by the bot anymore)
**--** To delete a channel, simply navigate to the channel using the directory (or manually), channel options, and click Delete Channel. The bot will automatically update the directory. If not, use this command:
**----** `{BOT_PREFIX}update`
"""

            elif subsection.lower() == "create_channel":
                em.description = f"""
**CREATE_CATEGORY**; Aliases: "new_cat"
`{BOT_PREFIX}create_category <directory> <name>`
------------------------------
Create a new category under `directory` with the name `name`.
**--** It is recommended not to make 2 categories with the same name in the same directory! (This is not allowed by the bot anymore)
"""

            elif subsection.lower() == "delete_category":
                em.description = f"""
**DELETE_CATEGORY**; Aliases: "del_cat"
`{BOT_PREFIX}delete_category <directory> <name>`
------------------------------
Delete a category, along with all channels within it.
**-- THIS ACTION CANNOT BE UNDONE.**
"""

            elif subsection.lower() == "rename_channel":
                em.description = f"""
**RENAME_CHANNEL**; Aliases: "rn_ch"
`{BOT_PREFIX}rename_channel <directory> <name> <rename>`
------------------------------
Rename the channel at the directory `directory` with name `name` to `rename`.
**--** You cannot rename to a channel already with the same name in the same directory.
"""

            elif subsection.lower() == "move_channel":
                em.description = f"""
**MOVE_CHANNEL**; Aliases: "mv_ch"
`{BOT_PREFIX}move_channel <directory> <name> <new_directory>`
------------------------------
Moves a channel or category at the directory `directory` with name `name` to the directory `new_directory`.
**--** You cannot move a channel or category if the destination already has a channel or category with that name.
"""

            elif subsection.lower() == "import_channel":
                em.description = f"""
**IMPORT_CHANNEL**; Aliases: "imp_ch"
`{BOT_PREFIX}import_channel <channel> <new_directory> <name>`
------------------------------
Imports an existing channel into the directory `new_directory` with the name `name`.
**--** Your channel will not be moved or changed.
**--** You cannot import a channel if the destination already has a channel or category with the name `name`.
"""
            elif subsection.lower() == "hide_channel":
                em.description = f"""
**HIDE_CHANNEL**; Aliases: "hd_ch"
`{BOT_PREFIX}hide_channel <directory> <name>`
------------------------------
Hide an existing channel from the directory `directory` with the name `name`.
**--** Your channel will not be moved, changed, or deleted.
**--** To make it appear again, use the `import_channel` command to import it back in a directory.
"""
            elif subsection.lower() == "save_directory":
                em.description = f"""
**SAVE_DIRECTORY**; Aliases: "save"
`{BOT_PREFIX}save_directory`
------------------------------
Save your current directory setup to a file to be loaded later at any time.
**--** This file contains pickled data using Python.
**--** To load said file, use the `{BOT_PREFIX}setup` command and attach the file to proceed.
**----** The process takes longer depending on how many channels are in the entire directory.
"""

            elif subsection.lower() == "preview_directory":
                em.description = f"""
**PREVIEW_DIRECTORY**; Aliases: "preview", "pvd"
`{BOT_PREFIX}preview_directory`
------------------------------
Sends you a Direct Message with a preview of a `cdr_directory.pkl` file.
**--** These are obtained using the `save_directory` command.
**--** Use this command if you are unsure what the structure of the file actually is.
"""
            elif subsection.lower() == "update":
                em.description = f"""
**UPDATE**
`{BOT_PREFIX}update`
------------------------------
Updates the directory channel.
**--** The more channels in the directory, the longer it takes to finish.
**----** During this time, no changes can be made to the directory.

**--** This command is automatically called when any channel in your server is deleted.
**----** If channels are being deleted faster than the bot can update, you may have to update it manually when you are done.

**--** The more channels that are deleted when calling this command, the longer it takes to finish.
**----** The system works by checking if a channel exists. If not, it updates internal memory and restarts.
"""

            elif subsection.lower() == "help":
                em.description = f"""
**HELP**
`{BOT_PREFIX}help [section] [subsection]`
------------------------------
Sends a help message.
**--** The `section` and `subsection` arguments:
**----** Typing `{BOT_PREFIX}help` will give you `section` names.
**----** If `section` is "commands", `subsection` help on a certain command.
"""

            elif subsection.lower() == "invite":
                em.description = f"""
**INVITE**
`{BOT_PREFIX}invite`
------------------------------
Sends an invite link to let me join a server.
"""
            else:
                em.description = f"Command {subsection.lower()} not found."
                em.color = 0xFF0000
        else:
            em.description = f"Section {section.lower()} not found."
            em.color = 0xFF0000

        await ctx.send(embed=em)
        print(f"[] Sent {section}, {subsection} help message to server \"{ctx.guild.name}\".")


def setup(bot: Bot):
    bot.add_cog(MiscCommands(bot))
