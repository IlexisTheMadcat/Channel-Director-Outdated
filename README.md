# Channel Director || Rem
## Nice to be of service.

### Introduction
I want to make a more convenient channel management system for you. *Pretty unique, isn't it?*
You can call me by prefixing your message with "cdr:"
Create a custom directory to better organize your channels.

**New? Try these commands in your server:**
```
cdr:setup
cdrLnew_channel "root" "Front Yard"
cdr:new_category "root" "Big House"
cdr:new_channel "root//Big House" "Livingroom"
```
**Required Permissions:**
```
"Manage Roles"    - To set the directory channel so that only the server owner may use it until further permissions are set.
"Manage Channels" - To create new channels.
"Manage Messages" - To manage the directory channel so that it's kept clean.
"Read Messages"   - To read commands.
"Send Messages"   - To send notifications/messages for warnings, confirmations, etc.
"Attach Files"    - To send the requested file from the command {BOT_PREFIX}save_directory.
```
*To see important announcements and command changes, Type and enter `{BOT_PREFIX}help updates`
Use this if you think a command isn't working the same way it did last time you used it.*

### Commands
Below is a list of all my commands. By each one is what permissions you need to run it yourself.
I am pretty smart so try not to exploit me.
```
Directory -- Control the directory setup
    setup             - You require the "Manage Server" and "M/Channels" permissions.
    teardown          - You require the "Manage Server" and "M/Channels" permissions.

Channels -- Manage channels in the directory
    create_channel    - You require the "Manage Channels" permission.
    create_category   - You require the "Manage Channels" permission.
    delete_category   - You require the "Manage Channels" permission.
    rename_channel    - You require the "Manage Channels" permission.
    move_channel      - You require the "Manage Channels" permission.
    import_channel    - You require the "Manage Channels" permission.
    hide_channel      - You require the "Manage Channels" permission.
    save_directory    - No Limits
    update            - You require the "Manage Channels" permission.

General -- General commands
    help              - No Limits
    invite            - No Limits
```
