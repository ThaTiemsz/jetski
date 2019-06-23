# Tags

The tags plugin provides tag management, for all your copypasta needs. Full credit goes to [Xenthys](https://github.com/Xenthys).

## Commands

| Name | Description | Default Level | Usage |
| :--- | :--- | :--- | :--- |
| `!tag list [pattern]` | List all the tags, with optional case-insensitive pattern matching | Trusted | `!tag list` OR `!tag list rul` |
| `!tag create {name} {content}` | Create a tag with the given content; or import one from [the GitHub repository](https://github.com/ThaTiemsz/RawgoatTags) using `import:<name>` as content | Trusted | `!tag create rules You should definitely read the #rules channel.` OR `!tag create sp import:shadowpres` |
| `!{name}` OR `!tag {name}` OR `!tag show {name}` | Show the content of a tag | Trusted | `!rules` OR `!tag rules` OR `!tag show rules` |
| `!tag raw {name}` | Show the raw tag, without any parsing | Trusted | `!tag raw rules` |
| `!tag info {name}` | Show info (content, author, uses) about a tag | Trusted | `!tag info rules` |
| `!tag debug {name}` | Show parsing debug information about a tag | Trusted | `!tag debug rules` |
| `!tag eval {content} --input [text] [--debug]` | Evaluate content with the tag parser | Trusted | `!tag eval Wow, {server_name} is really cool!` OR `!tag eval Wow, {input} is really cool --input "this server"` OR `!tag eval Wow, {input} is really cool --input "this server" --debug` |

## Variables

Variables are strings that will automatically be replaced when executing a tag.
Global mentions are escaped if the caller doesn't have the MENTION_EVERYONE permission.

| Variable | Description | Example |
| :--- | :--- | :--- |
| here | Literal @here | @here |
| everyone | Literal @everyone | @everyone |
| input | User-supplied input | anything |
| user | Caller's mention | @Tiemen#0001 |
| user\_id | Caller's ID | 152164749868662784 |
| user\_tag | Caller's tag | Tiemen#0001 |
| username | Caller's username | Tiemen |
| discriminator | Caller's discriminator | 0001 |
| nickname | Caller's nickname if any, else username | Tea man |
| avatar\_url | Caller's avatar URL | [https://cdn.discordapp.com/avatars/152164749868662784/8f0b7cdae1562928d44fd4f29ba66b8f.png](https://cdn.discordapp.com/avatars/152164749868662784/8f0b7cdae1562928d44fd4f29ba66b8f.png) |
| channel | Current channel's mention | #bot-spam |
| channel\_name | Current channel's name | #bot-spam |
| channel\_id | Current channel's ID | 411929226066001930 |
| bot\_nickname | The bot's nickname if any, else username | EM0J1B0T |
| server\_name | Current server's name | Blob Emoji |
| year | Current year | 2019 |
| month | Current month | 06 |
| day | Current day of the month | 23 |

Usage example: `!tag create welcome Hello {input}, welcome to **{server_name}**! {nickname} is happy to see you :blobwave:`

## Functions

Functions are variables that take parameters, and return a result based on them. They can be nested, but only up to 10 levels of depth at this time.
Parameters within functions all follow the same syntax, see examples in the table below for more information.

| Function | Parameters | Result | Example |
| :--- | :--- | :--- | :--- |
| random | int (a)\|int (b) | random number between `a` and `b`; order does not matter | `{random:0|5}` |
| choose | str\|str[\|str…] | random parameter | `{choose:pizza\|cheetos\|play\|sleep}` |
| repeat | int\|str | repeat `int` times `str` | `{repeat:42\|meow }` |
| set | str\|str | store data, first `str` is the key, second is the data (which can contain the `\|` character) | `{set:number\|{random:0\|5}}` |
| get | str[\|int] | fetch stored data, empty if data doesn't exist; `int` to wait for inner depths to resolve | `{get:number}` OR `{get:number\|2}` (delay execution by 2 iterations / levels of depth) |
| isnumber | str | `str` if it's a positive integer, empty otherwise | `{isnumber:{input}}` |
| mention | str | `str` if it's a user or role mention, empty otherwise | `{mention:{input}}` |
| match | str (a)\|str (b)[\|str (mode)] | `a` if `a` and `b` are identical (case insensitive), empty otherwise; supports an optional mode (`begin`, `end`, `contain`) to check if `a` begins by / ends by / contains `b` | `{match:{input}\|meow}` OR `{match:{input}\|348350443031625738\|contain}` |
| input | [int\|int] | substring of the actual `input` variable (if any) | `{input:2}` (second word) OR `{input:2\|}` (first 2 words) OR `{input:2\|4}` (second to fourth word) OR `{input:2\|-3}` (second to the end minus the latest 3 words) OR `{input:\|2}` (latest 2 words) OR `{input:\|-2}` (whole input minus the latest 2 words) |
| if | str (cond)\|str (valid)[\|str (invalid)] | `valid` if `cond` exists, `invalid` otherwise (both can be empty); `cond` can also be a simple comparison (`=`, `<` or `>`) between two numbers, in which no spacing is allowed | `{if:{input}\|{input}\|fellow blob}` OR `{if:{random:0\|3}\|\|:photoblob:}` (25% chance of printing ":photoblob:", else nothing) |
| math | int (a)\|str (operator)\|int (b) | perform simple math operations, default output is `0`; supported operators: `+`, `-`, `*`, `/`, `%` - no spacing is allowed | `{math:3*5}` OR `{math:{input:1}{input:2}{input:3}}` |
| and | str (a)\|str (b) | `a` if both `a` and `b` exist, empty otherwise | `{and:{input:1}\|{input:2}}` |
| or | str (a)\|str (b) | `a` if `a` exists, else `b` if `b` exists, empty otherwise | `{or:{match:{input}\|blue}\|{match:{input}\|green}}` |

## Configuration Options

| Option | Description | Type | Default |
| :--- | :--- | :--- | :--- |
| max\_tag\_length | Maximum length of a tag's content | int | empty |
| min\_level\_remove\_others | Minimum level to allow users to remove other users' tags | int | 50 |

## Configuration Example

```text
  tags:
    max_tag_length: 1337
    min_level_remove_others: 50
```
