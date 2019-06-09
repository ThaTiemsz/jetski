# Reminders

The reminders plugin provides reminder commands.

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
      <td style="text-align:left"><code>!r add {duration} {content}</code> OR <code>!remind {duration} {content}</code>
      </td>
      <td style="text-align:left">Adds a reminder. Bot will mention the user after the specified duration
        with the given message</td>
      <td style="text-align:left">Default</td>
      <td style="text-align:left"><code>!r add 24h update announcements</code> OR <code>!remind 24h update announcements</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left">
        <p><code>!r clear</code>
        </p>
        <p>OR</p>
        <p><code>!r clear all</code>
        </p>
        <p>OR</p>
        <p><code>!r clear global all</code>
        </p>
      </td>
      <td style="text-align:left">Clears all of the user&apos;s reminders set in a server, or globally</td>
      <td
      style="text-align:left">Default</td>
        <td style="text-align:left"><code>!r clear</code>
        </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!r clear {ID}</code>
      </td>
      <td style="text-align:left">Clear a reminder</td>
      <td style="text-align:left">Default</td>
      <td style="text-align:left"><code>!r clear 8</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left">
        <p><code>!r list [limit]</code>
        </p>
        <p>OR</p>
        <p><code>!reminders [limit]</code>
        </p>
        <p>OR</p>
        <p><code>!r list [global] [limit]</code>
        </p>
      </td>
      <td style="text-align:left">Returns a list of your reminders. Limits the number of reminders shown
        if specified</td>
      <td style="text-align:left">Default</td>
      <td style="text-align:left">
        <p><code>!r list</code>
        </p>
        <p>OR</p>
        <p><code>!reminders</code>
        </p>
        <p>OR</p>
        <p><code>!r list 1</code>
        </p>
        <p>OR</p>
        <p><code>!r list global</code>
        </p>
      </td>
    </tr>
  </tbody>
</table>## Configuration Example

```text
reminders: {}
```

There is no further configuration for this plugin.

