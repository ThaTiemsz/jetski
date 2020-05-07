# Utility

The utility plugin provides a number of useful and fun commands.

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
      <td style="text-align:left"><code>!cat</code>
      </td>
      <td style="text-align:left">Returns a random image of a cat</td>
      <td style="text-align:left">Default</td>
      <td style="text-align:left"><code>!cat</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!emoji {emoji}</code>
      </td>
      <td style="text-align:left">Returns information on the given emoji</td>
      <td style="text-align:left">Default</td>
      <td style="text-align:left"><code>!emoji :smiley:</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!geoip {ip}</code>
      </td>
      <td style="text-align:left">Searches given IP and returns information on its location</td>
      <td style="text-align:left">Default</td>
      <td style="text-align:left"><code>!geoip 8.8.8.8</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!info [user]</code>
      </td>
      <td style="text-align:left">Returns information on the given user</td>
      <td style="text-align:left">Default</td>
      <td style="text-align:left"><code>!info 232921983317180416</code> OR <code>!info @rowboat#0001</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!jumbo {emojis}</code>
      </td>
      <td style="text-align:left">Returns 128x128px images of the given emoji</td>
      <td style="text-align:left">Default</td>
      <td style="text-align:left"><code>!jumbo :cat: :dog: :rabbit:</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!pwnd {email}</code>
      </td>
      <td style="text-align:left">Searches given email on haveibeenpwnd.com and returns results</td>
      <td
      style="text-align:left">Default</td>
        <td style="text-align:left"><code>!pwnd johndoe@gmail.com</code>
        </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!random coin</code>
      </td>
      <td style="text-align:left">Flips a coin and returns the result</td>
      <td style="text-align:left">Default</td>
      <td style="text-align:left"><code>!random coin</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!random number [end number] [start number]</code>
      </td>
      <td style="text-align:left">Returns a random number from 0-10 or in a range if specified</td>
      <td style="text-align:left">Default</td>
      <td style="text-align:left"><code>!random number</code> OR <code>!random number 50 20</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!search {query}</code>
      </td>
      <td style="text-align:left">Searches for usernames that match given query</td>
      <td style="text-align:left">Default</td>
      <td style="text-align:left"><code>!search b1nzy</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!seen {user}</code>
      </td>
      <td style="text-align:left">Returns the timestamp of when the bot last saw a message from given user</td>
      <td
      style="text-align:left">Default</td>
        <td style="text-align:left"><code>!seen 232921983317180416</code> OR <code>!seen @rowboat#0001</code>
        </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!server [guild]</code>
      </td>
      <td style="text-align:left">Returns information on the current server or the Server ID if given</td>
      <td
      style="text-align:left">Default</td>
        <td style="text-align:left"><code>!server</code> OR <code>!server 290923757399310337</code>
        </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!urban {term}</code>
      </td>
      <td style="text-align:left">Searches given term on Urban Dictionary and returns the highest voted
        definition</td>
      <td style="text-align:left">Default</td>
      <td style="text-align:left">
        <br /><code>!urban word</code>
      </td>
    </tr>
    <tr>
      <td style="text-align:left"><code>!avatar [user]</code>
      </td>
      <td style="text-align:left">Returns the profile picture of the given user</td>
      <td style="text-align:left">Default</td>
      <td style="text-align:left">
        <p><code>!avatar 317853637374377985</code> OR</p>
        <p><code>!info @Jetski#2705</code>
        </p>
      </td>
    </tr>
  </tbody>
</table>## Configuration Example

```text
utilities: {}
```

There is no further configuration for this plugin.

