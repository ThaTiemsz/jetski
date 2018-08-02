# ModLog Plugin

The modlog plugin provides a mechanisim for logging various events and actions to one or more channels. The intention of the modlog is to provide a private feed of server events that administrators and moderators can use to better monitor and audit users actions. The modlog is extremely configurable, and thus fairly complex.

## Commands

| Name | Description | Default Level | Usage |
|------|-------------|---------------|-------|
| `!modlog hush` | Disables tracking of message deletes in modlog | Administrator | `!modlog hush` |
| `!modlog unhush` | Re-enables tracking of message deletes | Administrator | `!modlog unhush` |

## Configuration Options

| Option | Description | Type | Default |
|--------|-------------|------|---------|
| ignored\_users | A list of user ids which are ignored in the modlog. This is useful for ignoring bots that regularly delete or edit their messages | list | empty |
| ignored\_channels | A list of channel ids which are ignored in the modlog. This is useful for ignoring private or high-activity channels | list | empty |
| new\_member\_threshold | The number of seconds an account is considered new | int | 900 (15 minutes) |
| channels | Mapping of channel names/ids to ModLog Configurations | dict | empty |

### ModLog Configuration

| Option | Description | Type | Default |
|--------|-------------|------|---------|
| include | List of modlog actions to include. If empty this includes all mod log actions | list | empty |
| exclude | List of modlog actions to exclude. If empty this excludes no mod log actions | list | empty |
| timestamps | Whether to render timestamps along with loglines | bool | false |
| timezone | The timezone that timestamps are rendered in. Supported timezones: (https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568) | timezone | US/Eastern |

## Actions

| Action | Description |
|--------|-------------|
| CHANNEL\_CREATE | A channel is created |
| CHANNEL\_DELETE | A channel is deleted |
| GUILD\_MEMBER\_ADD | A member joins |
| GUILD\_MEMBER\_REMOVE | A member leaves (or gets kicked) |
| GUILD\_ROLE\_CREATE | A role is created |
| GUILD\_ROLE\_DELETE | A role is deleted |
| GUILD\_BAN\_ADD | A ban is added |
| MEMBER\_ROLE\_ADD | A role is added to a member |
| MEMBER\_ROLE\_RMV | A role is removed from a member |
| MEMBER\_TEMP\_MUTED | A tempmute is added |
| MEMBER\_MUTED | A mute is added |
| MEMBER\_UNMUTED | A mute is removed |
| MEMBER\_KICK | A member is kicked |
| MEMBER\_BAN | A ban (with a reason) is added |
| MEMBER_SOFTBAN | A softban is added |
| MEMBER_TEMPBAN | A tempban is added |
| MEMBER_WARNED | A warning is added |
| MEMBER\_RESTORE | A user rejoined and had their roles/nickname/etc restored |
| ADD\_NICK | A user adds a nickname |
| RMV\_NICK | A user removes a nickname |
| CHANGE\_NICK | A user changes their nickname |
| CHANGE\_USERNAME | A user changes their username |
| MESSAGE\_EDIT | A message is edited |
| MESSAGE\_DELETE | A message is deleted |
| MESSAGE\_DELETE\_BULK | Multiple messages are deleted |
| VOICE\_CHANNEL\_JOIN | A user joins a voice channel |
| VOICE\_CHANNEL\_LEAVE | A user leaves a voice channel |
| VOICE\_CHANNEL\_MOVE | A user moves voice channels |
| COMMAND\_USED | A user uses a rowboat command |
| SPAM\_DEBUG | A user triggered spam protection |
| CENSORED | A user posted a message that was censored by the bot |

## Configuration Example

```
  modlog:
    channels:
      289494042000228352:
        timestamps: true
        timezone: Etc/GMT-8
        exclude: []
        include: []
    ignored_users: [202217402635780096]
    new_member_threshold: 86400
```
