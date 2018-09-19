# Moderator

The admin plugin provides a set of useful moderator commands. These commands are intended to be used together and help handle/track misbehaving users over time.

## Commands

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
      <td style="text-align:left"><code>!warn {user} [reason]</code>
      </td>
      <td style="text-align:left">Adds a warning infraction to a user</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!warn 232921983317180416 1st warning, spamming emoji</code> OR <code>!warn @rowboat#0001 2nd warning, going off-topic</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!mute {user} [reason]</code>
      </td>
      <td style="text-align:left">Mutes a user. This will only work if <code>mute_role</code> is set in the
        config</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!mute 232921983317180416 spamming</code> OR <code>!tempmute @rowboat#0001 60m spamming</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!unmute {user}</code>
      </td>
      <td style="text-align:left">Unmutes a user</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!unmute 232921983317180416</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!tempmute {user} {duration} [reason]</code>
      </td>
      <td style="text-align:left">Temporarily mutes a user. Will only work if <code>temp_mute_role</code> or <code>mute_role</code> is
        set in the config</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!tempmute 232921983317180416 30m spamming</code> OR <code>!tempmute @rowboat#0001 30m spamming</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!kick {user} [reason]</code>
      </td>
      <td style="text-align:left">Kicks the user from the server</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!kick 232921983317180416 spamming</code> OR <code>!kick @rowboat#0001 spamming</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!mkick {users} -r [reason]</code>
      </td>
      <td style="text-align:left">Kicks multiple users from the server</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!mkick 232921983317180416 80351110224678912 108598213681922048 -r spamming</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!ban {user} [reason]</code>
      </td>
      <td style="text-align:left">Bans a user from the server</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!ban 232921983317180416 spamming</code> OR <code>!ban @rowboat#0001 spamming</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!mban {users} -r [reason]</code>
      </td>
      <td style="text-align:left">Ban multiple users from the servers</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!mban 232921983317180416 80351110224678912 108598213681922048 -r raid</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!unban {user} [reason]</code>
      </td>
      <td style="text-align:left">Unbans a user</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!unban 232921983317180416</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!forceban {User ID} [reason]</code>
      </td>
      <td style="text-align:left">Force bans a user who is not currently in the server</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!forceban 232921983317180416 spamming</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!softban {user} [reason]</code>
      </td>
      <td style="text-align:left">Softbans (bans/unbans) a user and deletes the user's messages sent within
        the last 7 days</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!softban 232921983317180416 spamming</code> OR <code>!softban @rowboat#0001 spamming</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!tempban {user} {duration} [reason]</code>
      </td>
      <td style="text-align:left">Temporarily bans a user</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!tempban 232921983317180416 5h spamming</code> OR <code>!tempban @rowboat#0001 5h spamming</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!infractions archive</code>
      </td>
      <td style="text-align:left">Creates a CSV file of all infractions on the server</td>
      <td style="text-align:left">Administrator</td>
      <td style="text-align:left"><code>!infractions archive</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!infractions search {query}</code>
      </td>
      <td style="text-align:left">Searches infractions database for given query</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!infractions search 232921983317180416</code> OR <code>!infractions search rowboat#0001</code> OR <code>!infractions search spamming</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!infractions info {inf#}</code>
      </td>
      <td style="text-align:left">Presents information on the given infraction</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!infractions info 1274</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!infractions duration {inf#} {duration}</code>
      </td>
      <td style="text-align:left">Updates the duration of the given infraction. Duration starts from time
        of initial action</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!infractions duration 1274 5h</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!reason {inf#} {reason}</code>
      </td>
      <td style="text-align:left">Updates the reason of a given infraction</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!infractions reason 1274 rude behaviour towards staff</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!backups restore {user}</code>
      </td>
      <td style="text-align:left">Restore a member's roles/nickname etc.</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!backups restore 152164749868662784</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!backups clear {User ID}</code>
      </td>
      <td style="text-align:left">Clear a member's backup</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left"><code>!backups clear 152164749868662784</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!slowmode {interval} [channel]</code>
      </td>
      <td style="text-align:left">Enable the built-in slowmode feature. Set to 0 to disable.</td>
      <td style="text-align:left">Moderator</td>
      <td style="text-align:left">
        <p><code>!slowmode 5</code>
        </p>
        <p>OR</p>
        <p><code>!slowmode 120 #general</code>
        </p>
      </td>
    </tr>
  </tbody>
</table>## Configuration Options

| Option | Description | Type | Default |
| :--- | :--- | :--- | :--- |
| confirm\_actions | Whether to confirm that an action was done in the current channel | bool | true |
| confirm\_actions\_reaction | Whether to confirm actions done in the channel using a checkmark reaction | bool | false |
| confirm\_actions\_expiry | The duration after which to delete the confirmed action message. If zero the message will never be deleted | int | 0 |
| mute\_role | Role ID that is set for users who are muted | id | none |
| reason\_edit\_level | Minimum level to allow users to edit other users' infraction reasons | int | 100 |

## Configuration Example

```text
  infractions:
    confirm_actions: false
    mute_role: 289494296703533058
    reason_edit_level: 50
```

