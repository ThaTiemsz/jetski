# Starboard Plugin

The starboard plugin provides an ongoing board of highlighted messages through community voting.

## Commands

| Name | Description | Default Level | Usage |
|------|-------------|---------------|-------|
| `!stars show {mid}` | Displays the given starred message | Trusted | `!stars show 320312743842545664` |
| `!stars stats [user]` | Presents starboard statistics for the whole server or the given user | Moderator | `!stars stats` OR `!stars stats 232921983317180416` |
| `!stars block {user}` | Prevents the user from starring any messages and prevents their messages from being starred | Moderator | `!stars block @rowboat#0001` OR `!stars block 232921983317180416` |
| `!stars unblock {user}` | Unblocks a user from the starboard | Moderator | `!stars unblock @rowboat#0001` OR `!stars unblock 232921983317180416` |
| `!stars hide {mid}` | Hides a starred message from the starboard | Moderator | `!stars hide 320312743842545664` |
| `!stars unhide {mid}` | Unhides a hidden message | Moderator | `!stars unhide 320312743842545664` |
| `!stars lock` | Prevents any new starred messages from being posted to the starboard | Administrator | `!stars lock` |
| `!stars unlock` | Enables starred messages to be posted | Administrator | `!stars unlock` |
| `!stars check {mid}` | Updates star reaction count on given message | Administrator | `!stars check 320312743842545664` |
| `!stars update` | Updates reaction count for the whole starboard | Administrator | `!stars update` |


## Configuration Options

| Option | Description | Type | Default |
|--------|-------------|------|---------|
| channels | A mapping of channels to Starboard Configurations | dict | empty |

### Starboard Configuration

| Option | Description | Type | Default |
|--------|-------------|------|---------|
| channels | Sets which channel starred messages should be posted to | dict | empty |
| clear\_on\_delete | Whether a starboard entry is deleted if the original message is deleted | bool | true |
| min\_stars | Minimum number of star reactions required before a message is posted to the starboard | int | 1 |
| star\_color\_max | Sets the "max" star level. Changes shading of rich embed bar color per level and gives the starboard entry a different emoji at max level | int | 15 |
| prevent\_self\_star | Whether to prevent a user from starring their own message | bool | false |

## Configuration Example

```
  starboard:
    channels:
      301118039326457867:
        clear_on_delete: true
        min_stars: 6
        star_color_max: 15
        prevent_self_star: true
```
