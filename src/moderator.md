# Moderator Command Quick-Reference

## Punishments

| Name | Description | Default Level | Usage |
|------|-------------|---------------|-------|
| `!warn {user} [reason]` | Adds a warning infraction to a user | Moderator | `!warn 232921983317180416 1st warning, spamming emoji` OR `!warn @rowboat#0001 2nd warning, going off-topic` |
| `!mute {user} [reason]` | Mutes a user. This will only work if `mute_role` is set in the config | Moderator | `!mute 232921983317180416 spamming` OR  `!tempmute @rowboat#0001 60m spamming` |
| `!unmute {user}` | Unmutes a user | Moderator | `!unmute 232921983317180416` |
| `!tempmute {user} {duration} [reason]` | Temporarily mutes a user. Will only work if `temp_mute_role` or `mute_role` is set in the config | Moderator | `!tempmute 232921983317180416 30m spamming` OR `!tempmute @rowboat#0001 30m spamming` |
| `!kick {user} [reason]` | Kicks the user from the server | Moderator | `!kick 232921983317180416 spamming` OR `!kick @rowboat#0001 spamming` |
| `!ban {user} [reason]` | Bans a user from the server | Moderator | `!ban 232921983317180416 spamming` OR `!ban @rowboat#0001 spamming` |
| `!unban {user} [reason]` | Unbans a user | Moderator | `!unban 232921983317180416` |
| `!forceban {User ID} [reason]` | Force bans a user who is not currently in the server | Moderator | `!forceban 232921983317180416 spamming` |
| `!softban {user} [reason]` | Softbans (bans/unbans) a user and deletes the user's messages sent within the last 7 days | Moderator | `!softban 232921983317180416 spamming` OR `!softban @rowboat#0001 spamming` |
| `!tempban {user} {duration} [reason]` | Temporarily bans a user | Moderator | `!tempban 232921983317180416 5h spamming` OR `!tempban @rowboat#0001 5h spamming` |


## Admin Utilities

| Name | Description | Default Level | Usage |
|------|-------------|---------------|-------|
| `!clean all [count]` | Cleans (deletes) [count] many messages in the current channel | Moderator | `!clean all 20` |
| `!clean user {user} [count]` | Cleans [count] many messages a given user sent in the current channel | Moderator | `!clean user 232921983317180416 50` |
| `!clean bots [count]` | Cleans [count] many messages sent by bots in the current channel | Moderator | `!clean bots 30` |
| `!clean cancel` | Cancels any cleaning process running in current channel | Moderator | `!clean cancel` |
| `!reactions clean {user} [count] [emoji]` | Removes the most recent count of reactions from a given user | Moderator | `!reactions clean 232921983317180416` OR `!reactions clean @rowboat#0001 30` OR `!reactions clean 232921983317180416 20 :thinking:` |
| `!archive (here / all) [count]` | Archives [count] many messages in the current channel | Moderator | `!archive all 50` OR `!archive here 50` |
| `!archive user {user} [count]` | Archives [count] many messages that a given user sent in the current guild | Moderator | `!archive user 232921983317180416 100` OR `!archive user @rowboat#0001 100` |
| `!archive channel {channel} [count]` | Archives [count] many messages in the given channel | Moderator | `!archive channel 289482554250100736 20` |
| `!search {query}` | Searches for usernames that match given query | Default | `!search b1nzy` |
| `!role add {user} {role} [reason]` | Adds a role to a user | Moderator | `!role add 232921983317180416 Moderator Promotion from Member` OR `!role add rowboat#0001 Admin Pretty good Moderator` |
| `!role remove {user} {role} [reason]` | Removes a role from a user | Moderator | `!role remove 232921983317180416 Administrator Demoted for being bad at job` OR `!role remove rowboat#0001 Mod Terrible moderator` |
| `!r add {duration} {content}` OR `!remind {duration} {content}` | Adds a reminder. Bot will mention the user after the specified duration with the given message | Default | `!r add 24h update announcements` OR `!remind 24h update announcements` |
| `!r clear` | Clears all of the user's reminders | Default | `!r clear` |
| `!voice log {user}` | Displays a list of a given user's recent voice channel activity | Moderator | `!voice log 232921983317180416` OR `!voice log @rowboat#0001` |


## Infractions

| Name | Description | Default Level | Usage |
|------|-------------|---------------|-------|
| `!infractions search {query}` | Searches infractions database for given query | Moderator | `!infractions search 232921983317180416` OR `!infractions search rowboat#0001` OR `!infractions search spamming`
| `!infractions info {inf#}` | Presents information on the given infraction | Moderator | `!infractions info 1274`
| `!infractions duration {inf#} {duration}` | Updates the duration of the given infraction. Duration starts from time of initial action | Moderator | `!infractions duration 1274 5h` |
| `!reason {inf#} {reason}` | Updates the reason of a given infraction | Moderator | `!reason 1274 rude behaviour towards staff` |


## Starboard

| Name | Description | Default Level | Usage |
|------|-------------|---------------|-------|
| `!stars block {user}` | Prevents the user from starring any messages and prevents their messages from being starred | Moderator | `!stars block @rowboat#0001` OR `!stars block 232921983317180416` |
| `!stars unblock {user}` | Unblocks a user from the starboard | Moderator | `!stars unblock @rowboat#0001` OR `!stars unblock 232921983317180416` |
| `!stars hide {mid}` | Hides a starred message from the starboard | Moderator | `!stars hide 320312743842545664` |
| `!stars unhide {mid}` | Unhides a hidden message | Moderator | `!stars unhide 320312743842545664` |
| `!stars lock` | Prevents any new starred messages from being posted to the starboard | Administrator | `!stars lock` |
| `!stars unlock` | Enables starred messages to be posted | Administrator | `!stars unlock` |
