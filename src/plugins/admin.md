# Admin Plugin

The admin plugin provides a set of administrator commands that help in moderating active servers.

## Commands

| Name | Description | Default Level | Usage |
|------|-------------|---------------|-------|
| `!join / add / give {role}` | Assigns a role if it's listed in the group_roles config setting | Default | `!join PC` OR `!add Console` OR `!give Tabletop` |
| `!leave / remove / take {role}` | Removes a group role from a user | Default | `!leave PC` OR `!remove Console` OR `!take Tabletop` |
| `!temprole {user} {role ID} {duration} [reason]` | Temporarily applies a role to a user | Moderator | `!temprole 232921983317180416 295646805650046977 7d Trial Mod` OR `!temprole @rowboat#0001 295646805650046977 24h Member of the Day` |
| `!roles` | Returns a list of ids/names for all roles on the server. Useful for configuring other rowboat plugins | Moderator | `!roles` |
| `!role add {user} {role} [reason]` | Adds a role to a user | Moderator | `!role add 232921983317180416 Moderator Promotion from Member` OR `!role add rowboat#0001 Admin Pretty good Moderator` |
| `!role remove {user} {role} [reason]` | Removes a role from a user | Moderator | `!role remove 232921983317180416 Administrator Demoted for being bad at job` OR `!role remove rowboat#0001 Mod Terrible moderator` |
| `!role unlock {role ID}` | Unlocks a role listed in the locked_roles config setting for 5 minutes, allowing permission updates | Administrator | `!role unlock 346471724126044160` |
| `!archive (here / all) [count]` | Archives [count] many messages in the current channel | Moderator | `!archive all 50` OR `!archive here 50` |
| `!archive user {user} [count]` | Archives [count] many messages that a given user sent in the current guild | Moderator | `!archive user 232921983317180416 100` OR `!archive user @rowboat#0001 100` |
| `!archive channel {channel} [count]` | Archives [count] many messages in the given channel | Moderator | `!archive channel 289482554250100736 20` |
| `!clean all [count]` | Cleans (deletes) [count] many messages in the current channel | Moderator | `!clean all 20` |
| `!clean user {user} [count]` | Cleans [count] many messages a given user sent in the current channel | Moderator | `!clean user 232921983317180416 50` |
| `!clean bots [count]` | Cleans [count] many messages sent by bots in the current channel | Moderator | `!clean bots 30` |
| `!clean cancel` | Cancels any cleaning process running in current channel | Moderator | `!clean cancel` |
| `!reactions clean {user} [count] [emoji]` | Removes the most recent count of reactions from a given user | Moderator | `!reactions clean 232921983317180416` OR `!reactions clean @rowboat#0001 30` OR `!reactions clean 232921983317180416 20 :thinking:` |
| `!backups restore {user}` | Restores a user to the most recently saved member backup | Moderator | `!backups restore 232921983317180416` OR `!backups restore rowboat#0001` |
| `!backups clear {user ID}` | Deletes all saved backups for a user | Moderator | `!backups clear 232921983317180416` OR `!backups clear rowboat#0001` |
| `!stats {user}` | Presents general statistics for a given user | Moderator | `!stats 232921983317180416` OR `!stats rowboat#0001` |
| `!emojistats (global / server) most` | Displays the most / least used server emojis in the current guild / globally | Moderator | `!emojistats global most` OR `!emojistats server least` |
| `!voice log {user}` | Displays a list of a given user's recent voice channel activity | Moderator | `!voice log 232921983317180416` OR `!voice log @rowboat#0001` |
| `!invites prune [uses]` | Deletes server invites with the given number of uses or less. Cleans 1 and 0 use invites if left blank | Administrator | `!invites prune 5` |


## Configuration Options

| Option | Description | Type | Default |
|--------|-------------|------|---------|
| role\_aliases | Aliases which can be used in place of role IDs in commands | dict | empty |
| group\_roles | Roles which can be joined and left by any user. These roles cannot grant any elevated permissions | dict | empty |
| locked\_roles | Prevents permission changes from being made to listed roles | list | empty |
| persist | Controls the member persistance settings | dict | empty |

### Member Persistance Settings

| Option | Description | Type | Default |
|--------|-------------|------|---------|
| roles | Whether to recover roles when a user rejoins the server | bool | false |
| role\_ids | A list of role ids which will be recovered if `roles` is true. Any other roles will be ignored when a user rejoins the server | list | empty |
| nickname | Whether to recover the nickname when a user rejoins the server | bool | false |
| voice | Whether to recover mute/deafen settings when a user rejoins the server | bool | false |


## Configuration Example

```
  admin:
    persist:
      roles: true
      role_ids: [278810978722906112, 278972423502561280, 278972377587515392]
      nickname: true
      voice: false
    role_aliases:
      role1: 205769314199011329
      role2: 333806119199703042
    group_roles:
      PC: 278810978722906112
      Console: 278972377587515392
      Tabletop: 278972423502561280
    locked_roles: [346471724126044160, 252184905075654657]
```
