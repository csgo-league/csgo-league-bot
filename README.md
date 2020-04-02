[![HitCount](http://hits.dwyl.io/csgo-league/csgo-queue-bot.svg)](http://hits.dwyl.io/csgo-league/csgo-queue-bot)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/csgo-league/csgo-queue-bot/graphs/commit-activity)
[![GitHub release](https://img.shields.io/github/release/csgo-league/csgo-queue-bot.svg)](https://github.com/csgo-league/csgo-queue-bot/releases/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![Open Source Love svg3](https://badges.frapsoft.com/os/v3/open-source.svg?v=103)](https://github.com/csgo-league)

# CS:GO League Bot
A Discord bot to manage CS:GO PUGs. Connects to the CS:GO League web API.

Our support discord can be found [here](https://discord.gg/b5MhANU).

# Author
[cameronshinn](https://github.com/cameronshinn) - Developer / Maintainer

## Watch for releases

So as to keep the latest version of the plugin I recommend watching the repository

![Watch releases](https://github.com/b3none/gdprconsent/raw/development/.github/README_ASSETS/watch_releases.png)

## Share the love

If you appreciate the project then please take the time to star our repository.

![Star us](https://github.com/b3none/gdprconsent/raw/development/.github/README_ASSETS/star_us.png)

## Setup
1. First you must have a bot instance to run this script on. Follow Discord's tutorial [here](https://discord.onl/2019/03/21/how-to-set-up-a-bot-application/) on how to set one up. Be sure to invite it to a server to use it.

   * The permissions integer necessary is `17067072`.

2. Get an API token for the CS:GO League [web API](https://github.com/csgo-league/csgo-league-web) along with the host URL.

3. (Optional) If you have a Discord Bot List token to use with [top.gg](https://top.gg/) then retrieve that from its editing menu.

4. Run `pip3 install -r requirements.txt` in the repository's root directory to get the necessary libraries.

    * Note that python-Levenshtein requires your system to have a C++ compiler (Visual Studio C++ compiler for Windows or g++ for Linux). This library may be replaced in the future to eliminate this requirement.

5. Add the `/qbot` path to your `PYTHONPATH` environment variable to be able to import it from anywhere.

6. Using your bot's Discord token, League web server URL, League API token and Discord Bot List token, run the bot like so...

```python
import qbot

DISCORD_TOKEN = 'XXXXXXXX'
API_BASE_URL = 'XXXXXXXX'
API_KEY = 'XXXXXXXX'
DBL_TOKEN = 'XXXXXXXX'
qbot.run(DISCORD_TOKEN, API_BASE_URL, API_KEY, dbl_token=DBL_TOKEN)
```

Now you are ready to start using the League CS:GO Queue Bot! Try out some of the commands to make sure it works.

*Note that currently the `mdraft` command depends on custom emojis to be used as buttons which are hardcoded [here](https://github.com/csgo-league/csgo-queue-bot/blob/abb06e1876546bb3948094faa795e90184642882/qbot/cogs/mapdraft.py#L20). As of right now you will need to make the emojis yourself and replace the emoji code in the map objects there.*

## Commands
`q!help` **-** Display help menu<br>

`q!about` **-** Display basic info about this bot<br>

`q!join` **-** Join the queue<br>

`q!leave` **-** Leave the queue<br>

`q!view` **-** Display who is currently in the queue<br>

`q!remove <mention>` **-** Remove the mentioned user from the queue (must have server kick perms)<br>

`q!empty` **-** Empty the queue (must have server kick perms)<br>

`q!cap <integer>` **-** Set the capacity of the queue to the specified value (must have admin perms)<br>

`q!tdraft` **-** Start (or restart) a team draft from the last popped queue<br>

`q!mdraft` **-** Start (or restart) a map draft<br>

`q!setmp {+|-}<map name> ...` **-** Add or remove maps from the mdraft map pool (Must have admin perms)<br>

`q!donate` **-** Link the bot's donation link<br>

## Contributions

### Code Style
This project adheres to the [PEP8 style guide](https://www.python.org/dev/peps/pep-0008/) with 120 character line limits.

### Branches
Create a branch if you're working on an issue with the issue number and name like so: `100_Title-Separated-By-Dashes`.

### Commit Messages
Phrase commits in the present tense, e.g. `Fix bug` instead of `Fixed bug`.
