[![HitCount](http://hits.dwyl.io/csgo-league/csgo-league-bot.svg)](http://hits.dwyl.io/csgo-league/csgo-league-bot)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/csgo-league/csgo-league-bot/graphs/commit-activity)
[![GitHub release](https://img.shields.io/github/release/csgo-league/csgo-league-bot.svg)](https://github.com/csgo-league/csgo-league-bot/releases/)
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

2. Setup and get an API token for the CS:GO League [web API](https://github.com/csgo-league/csgo-league-web) along with the host base URL.

3. Install libpq-dev (Linux only?). This is needed to install the psycopg2 Python package.

    * Linux command is `sudo apt-get install libpq-dev`.

3. Run `pip3 install -r requirements.txt` in the repository's root directory to get the necessary libraries.

    * Note that python-Levenshtein requires your system to have a C++ compiler (Visual Studio C++ compiler for Windows or g++ for Linux). This library may be replaced in the future to eliminate this requirement.

4. Install PostgreSQL 9.5 or higher.

    * Linux command is `sudo apt-get install postgresql`.
    * Windows users can download [here](https://www.postgresql.org/download/windows).

5. Run the psql tool (`sudo -u postgres psql` on Linux) and create a database by running the following commands:

    ```sql
    CREATE ROLE csgoleague WITH LOGIN PASSWORD 'yourpassword';
    CREATE DATABASE csgoleague OWNER csgoleague;
    ```

    Be sure to replace `'yourpassword'` with your own desired password.

5. Create an environment file named `.env` with in the repository's root directory. Fill this template with the requisite information you've gathered:

    ```env
    DISCORD_BOT_TOKEN=

    CSGO_LEAGUE_API_KEY=
    CSGO_LEAGUE_API_URL=

    POSTGRESQL_USER=
    POSTGRESQL_PASSWORD=
    POSTGRESQL_DB=
    POSTGRESQL_HOST=
    ```

    Optionally you may set these environment variables another way.

6. Apply the database migrations by running `python3 migrate.py up`.

7. Run the launcher Python script, `launcher.py`.

*Note that currently the `mdraft` command depends on custom emojis to be used as buttons which are hardcoded [here](https://github.com/csgo-league/csgo-league-bot/blob/abb06e1876546bb3948094faa795e90184642882/qbot/cogs/mapdraft.py#L20). As of right now you will need to make the emojis yourself and replace the emoji code in the map objects there.*

## Commands
`q!help` **-** Display help menu<br>

`q!about` **-** Display basic info about this bot<br>

`q!join` **-** Join the queue<br>

`q!leave` **-** Leave the queue<br>

`q!view` **-** Display who is currently in the queue<br>

`q!remove <mention>` **-** Remove the mentioned user from the queue (must have server kick perms)<br>

`q!empty` **-** Empty the queue (must have server kick perms)<br>

`q!cap <integer>` **-** Set the capacity of the queue to the specified value (must have admin perms)<br>

`q!setmp {+|-}<map name> ...` **-** Add or remove maps from the mdraft map pool (Must have admin perms)<br>

`q!donate` **-** Link the bot's donation link<br>

`q!stats` **-** See your stats<br>

`q!leaders` **-** See the top players in the server <br>

## Contributions

### Code Style
This project adheres to the [PEP8 style guide](https://www.python.org/dev/peps/pep-0008/) with 120 character line limits.

### Branches
Create a branch if you're working on an issue with the issue number and name like so: `100_Title-Separated-By-Dashes`.

### Commit Messages
Phrase commits in the present tense, e.g. `Fix bug` instead of `Fixed bug`.
