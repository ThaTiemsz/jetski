# Global Admin

All commands only usable by global administrators of the bot.

## Core

<table>
  <thead>
    <tr>
      <th style="text-align:left">Name</th>
      <th style="text-align:left">Description</th>
      <th style="text-align:left">Default Level</th>
      <th style="text-align:left">Usage</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="text-align:left"><code>!uptime</code>
      </td>
      <td style="text-align:left">Gets the bot&apos;s up time</td>
      <td style="text-align:left">Global Admin</td>
      <td style="text-align:left"><code>!uptime</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!source {command}</code>
      </td>
      <td style="text-align:left">Gets a link to the command in the source code on GitHub</td>
      <td style="text-align:left">Global Admin</td>
      <td style="text-align:left"><code>!source ban</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!eval {code}</code>
      </td>
      <td style="text-align:left">Evaluates code</td>
      <td style="text-align:left">Global Admin</td>
      <td style="text-align:left"><code>!eval msg.content</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!control sync-bans</code>
      </td>
      <td style="text-align:left">Sync bans from every guild</td>
      <td style="text-align:left">Global Admin</td>
      <td style="text-align:left"><code>!control sync-bans</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!control reconnect</code>
      </td>
      <td style="text-align:left">Reconnect to the gateway</td>
      <td style="text-align:left">Global Admin</td>
      <td style="text-align:left"><code>!control reconnect</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!guilds invite {guild ID}</code>
      </td>
      <td style="text-align:left">Generate a temporary invite to a server the bot is in</td>
      <td style="text-align:left">Global Admin</td>
      <td style="text-align:left"><code>!guilds invite 348832158590435328</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!guilds wh {guild ID}</code>
      </td>
      <td style="text-align:left">Whitelist a server (bot won&apos;t instantly leave)</td>
      <td style="text-align:left">Global Admin</td>
      <td style="text-align:left"><code>!guilds wh 348832158590435328</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!guilds unwh {guild ID}</code>
      </td>
      <td style="text-align:left">Unwhitelist a server</td>
      <td style="text-align:left">Global Admin</td>
      <td style="text-align:left"><code>!guilds unwh 348832158590435328</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!plugins disable / unload {name}</code>
      </td>
      <td style="text-align:left">Disable a plugin</td>
      <td style="text-align:left">Global Admin</td>
      <td style="text-align:left"><code>!plugins disable UtilitiesPlugin</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!plugins reload {name}</code>
      </td>
      <td style="text-align:left">Reload a plugin</td>
      <td style="text-align:left">Global Admin</td>
      <td style="text-align:left"><code>!plugins reload utilities</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!plugins enable / load {name}</code>
      </td>
      <td style="text-align:left">Load a plugin</td>
      <td style="text-align:left">Global Admin</td>
      <td style="text-align:left"><code>!plugins load admin</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left">
        <p><code>!plugins</code>
        </p>
        <p>OR</p>
        <p><code>!plugins list</code>
        </p>
      </td>
      <td style="text-align:left">List all loaded plugins</td>
      <td style="text-align:left">Global Admin</td>
      <td style="text-align:left"><code>!plugins list</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!nuke {user ID} {reason}</code>
      </td>
      <td style="text-align:left">Bans a user from every server bot is in</td>
      <td style="text-align:left">Global Admin</td>
      <td style="text-align:left"><code>!nuke 339793226166960129 alt</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!guilds wh-add {guild ID}</code>
      </td>
      <td style="text-align:left">Add a flag for a server</td>
      <td style="text-align:left">Global Admin</td>
      <td style="text-align:left"><code>!guilds wh-add 348832158590435328 modlog_custom_format</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!guilds wh-rmv {guild ID}</code>
      </td>
      <td style="text-align:left">Remove a flag a server</td>
      <td style="text-align:left">Global Admin</td>
      <td style="text-align:left"><code>!guilds wh-rmv 348832158590435328 modlog_custom_format</code>
      </td>
    </tr>
  </tbody>
</table>## Whitelist Flags

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

