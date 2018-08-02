# Spam Plugin

The spam plugin allows administrators and moderators to limit spam and enforce punishments on spammers. The plugin can be used to limit mass sending of:

- General Spam
- Mentions
- Links
- Attachments
- Emojis
- Newlines
- Duplicate Messages

## Configuration Options

| Option | Description | Type | Default |
|--------|-------------|------|---------|
| levels | A mapping of levels to Spam Configurations. This will match any user with a level that is equal or lower | dict | empty |

### Spam Configuration

| Option | Description | Type | Default |
|--------|-------------|------|---------|
| punishment | Sets which action is performed when the spam filter is triggered. Options are: NONE, MUTE, TEMPMUTE, BAN, TEMPBAN, KICK | str | none |
| punishment\_duration | Required for TEMPBAN and TEMPMUTE punishments and determines how many seconds a punishment should last | int | 300 |
| count | How many times an action should be performed for it to trigger the filter | int | ??? |
| interval | Time period within which the "count" of actions should be performed to trigger the filter | int | ??? |
| max\_messages | Total number of messages that can be sent | dict | empty |
| max\_mentions | How many user mentions can be sent | dict | empty |
| max\_links | How many links can be sent | dict | empty |
| max\_attachments | How many attachments can be sent | dict | empty |
| max\_emojis | How many emojis can be sent | dict | empty |
| max\_newlines | How many new lines/line breaks can be sent | dict | empty |
| max\_duplicates | How many duplicate messages can be sent | dict | empty |
| clean | Whether or not the offending messages which triggered spam detection should be deleted | bool | false |
| clean\_count | Maximum number of messages to be deleted | int | 100 |
| clean\_duration | Maximum duration (in seconds) for which to delete messages | int | 900 |

## Configuration Example

```
  spam:
    levels:
      0:
        punishment: TEMPMUTE
        punishment_duration: 120
        clean: true
        clean_count: 50
        clean_duration: 500
        max_messages:
          count: 10
          interval: 7
        max_mentions:
          count: 8
          interval: 30
        max_links:
          count: 10
          interval: 60
        max_attachments:
          count: 10
          interval: 60
        max_emojis:
          count: 100
          interval: 120
        max_newlines:
          count: 60
          interval: 120
        max_duplicates:
          count: 5
          interval: 30
```
