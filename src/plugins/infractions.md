# Infractions Plugin

The infractions plugin provides a set of useful moderator commands. These commands are intended to be used together and help handle/track misbehaving users over time.

## Commands

| Name | Description | Default Level | Usage |
|------|-------------|---------------|-------|
| `!warn {user} [reason]` | Adds a warning infraction to a user | Moderator | `!warn 232921983317180416 1st warning, spamming emoji` OR `!warn @rowboat#0001 2nd warning, going off-topic` |
| `!mute {user} [reason]` | Mutes a user. This will only work if `mute_role` is set in the config | Moderator | `!mute 232921983317180416 spamming` OR  `!tempmute @rowboat#0001 60m spamming` |
| `!unmute {user}` | Unmutes a user | Moderator | `!unmute 232921983317180416` |
| `!tempmute {user} {duration} [reason]` | Temporarily mutes a user. Will only work if `temp_mute_role` or `mute_role` is set in the config | Moderator | `!tempmute 232921983317180416 30m spamming` OR `!tempmute @rowboat#0001 30m spamming` |
| `!kick {user} [reason]` | Kicks the user from the server | Moderator | `!kick 232921983317180416 spamming` OR `!kick @rowboat#0001 spamming` |
| `!mkick {users] -r [reason]` | Kicks multiple users from the server | Moderator | `!mkick 232921983317180416 80351110224678912 108598213681922048 -r spamming` |
| `!ban {user} [reason]` | Bans a user from the server | Moderator | `!ban 232921983317180416 spamming` OR `!ban @rowboat#0001 spamming` |
| `!unban {user} [reason]` | Unbans a user | Moderator | `!unban 232921983317180416` |
| `!forceban {User ID} [reason]` | Force bans a user who is not currently in the server | Moderator | `!forceban 232921983317180416 spamming` |
| `!softban {user} [reason]` | Softbans (bans/unbans) a user and deletes the user's messages sent within the last 7 days | Moderator | `!softban 232921983317180416 spamming` OR `!softban @rowboat#0001 spamming` |
| `!tempban {user} {duration} [reason]` | Temporarily bans a user | Moderator | `!tempban 232921983317180416 5h spamming` OR `!tempban @rowboat#0001 5h spamming` |
| `!infractions archive` | Creates a CSV file of all infractions on the server | Administrator | `!infractions archive` |
| `!infractions search {query}` | Searches infractions database for given query | Moderator | `!infractions search 232921983317180416` OR `!infractions search rowboat#0001` OR `!infractions search spamming`
| `!infractions info {inf#}` | Presents information on the given infraction | Moderator | `!infractions info 1274`
| `!infractions duration {inf#} {duration}` | Updates the duration of the given infraction. Duration starts from time of initial action | Moderator | `!infractions duration 1274 5h` |
| `!reason {inf#} {reason}` | Updates the reason of a given infraction | Moderator | `!infractions reason 1274 rude behaviour towards staff` |

## Configuration Options

| Option | Description | Type | Default |
|--------|-------------|------|---------|
| confirm\_actions | Whether to confirm that an action was done in the current channel | bool | true |
| confirm\_actions\_reaction | Whether to confirm actions done in the channel using a checkmark reaction | bool | false |
| confirm\_actions\_expiry | The duration after which to delete the confirmed action message. If zero the message will never be deleted | int | 0 |
| mute\_role| Role ID that is set for users who are muted | id | none |
| reason\_edit\_level | Minimum level to allow users to edit other users' infraction reasons | int | 100 |

## Configuration Example

```
  infractions:
    confirm_actions: false
    mute_role: 289494296703533058
    reason_edit_level: 50
```
