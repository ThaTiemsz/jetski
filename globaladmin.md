# Global Admin

All commands only usable by global administrators of the bot.

## Core

| Name | Description | Default Level | Usage |
| :--- | :--- | :--- | :--- |
| `!uptime` | Gets the bot's up time | Global Admin | `!uptime` |
| `!source {command}` | Gets a link to the command in the source code on GitHub | Global Admin | `!source ban` |
| `!eval {code}` | Evaluates code | Global Admin | `!eval msg.content` |
| `!control sync-bans` | Sync bans from every guild | Global Admin | `!control sync-bans` |
| `!control reconnect` | Reconnect to the gateway | Global Admin | `!control reconnect` |
| `!guilds invite {guild ID}` | Generate a temporary invite to a server the bot is in | Global Admin | `!guilds invite 348832158590435328` |
| `!guilds wh {guild ID}` | Whitelist a server \(bot won't instantly leave\) | Global Admin | `!guilds wh 348832158590435328` |
| `!guilds unwh {guild ID}` | Unwhitelist a server | Global Admin | `!guilds unwh 348832158590435328` |
| `!plugins disable {name}` | Disable a plugin | Global Admin | `!plugins disable UtilitiesPlugin` |
| `!nuke {user ID} {reason}` | Bans a user from every server bot is in | Global Admin | `!nuke 339793226166960129 alt` |
| `!guilds wh-add {guild ID}` | Add a flag for a server | Global Admin | `!guilds wh-add 348832158590435328 modlog_custom_format` |
| `!guilds wh-rmv {guild ID}` | Remove a flag a server | Global Admin | `!guilds wh-rmv 348832158590435328 modlog_custom_format` |

## Whitelist Flags

| Key | Name |
| :--- | :--- |
| 1 | modlog\_custom\_format |

## Admin

| Name | Description | Default Level | Usage |
| :--- | :--- | :--- | :--- |
| `!infractions (delete / remove / del / rem / rm / rmv) {inf#}` | Delete an infraction | Global Admin | `!inf delete 29` |

## Modlog

| Name | Description | Default Level | Usage |
| :--- | :--- | :--- | :--- |
| `!modlog hush` | Disables tracking of message deletes in modlog | Global Admin | `!modlog hush` |
| `!modlog unhush` | Re-enables tracking of message deletes | Global Admin | `!modlog unhush` |

## Internal

| Name | Description | Default Level | Usage |
| :--- | :--- | :--- | :--- |
| `!commands errors` | Show recently occurring errors from command usage | Global Admin | `!commands errors` |
| `!commands info {message ID}` | Show more details on the command usage | Global Admin | `!commands info 516607133970595861` |
| `!commands usage` | Show most used commands \(globally\) | Global Admin | `!commands usage` |
| `!commands stats {command name}` | Show stats for a command | Global Admin | `!commands stats ban` |
| `!throw` | Throw an exception | Global Admin | `!throw` |
| `!events add {name}` | Track a gateway event | Global Admin | `!events add PRESENCE_UPDATE` |
| `!events remove {name}` | Stop tracking a gateway event | Global Admin | `!events remove PRESENCE_UPDATE` |

## SQL

| Name | Description | Default Level | Usage |
| :--- | :--- | :--- | :--- |
| `!sql {query}` | Execute an SQL query | Global Admin | `!sql SELECT content FROM messages WHERE message_id = 516758368329924608` |
| `!markov init {user / channel}` | Create a markov model of messages for a user or channel | Global Admin | `!markov init 152164749868662784` |
| `!markov one {user / channel}` | Get a message from the markov model | Global Admin | `!markov one 152164749868662784` |
| `!markov many {user / channel}` | Get multiple messages from the markov model | Global Admin | `!markov many 152164749868662784` |
| `!markov list` | List markov models | Global Admin | `!markov list` |
| `!markov delete {ID}` | Delete a markov model | Global Admin | `!markov delete 152164749868662784` |
| `!markov clear` | Clear all markov models | Global Admin | `!markov clear` |
| `!backfill message {channel ID} {message ID}` | Backfill a message | Global Admin | `!backfill message 260370329778520064 516758368329924608` |
| `!backfill reactions {message ID}` | Backfill reactions from a message | Global Admin | `!backfill reactions 516758368329924608` |
| `!backfill channel [channel ID]` | Backfill a channel | Global Admin | `!backfill channel 260370329778520064` |
| `!backfill guild [guild ID]` | Backfill a server | Global Admin | `!backfill guild 348832158590435328` |
| `!recover (global / here) {duration} [pool]` | Recover messages from all channels in a server or all servers | Global Admin | `!recover here 1h` |
| `!words usage {word} [unit] [amount]` | Show a chart of the usage of words | Global Admin | `!words usage hello` OR `!words usage hi days 14` |
| `!words top {user / channel / guild}` | Show a table of most used words | Global Admin | `!words top 152164749868662784` OR `!words top 260370329778520064` OR `!words top 348832158590435328` |

