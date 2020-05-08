# launcher.py

from bot.bot import LeagueBot
from bot.helpers.migrations import get_db

import asyncio
import configparser
import os.path
import sys


def get_config(filename):
    """"""
    config = configparser.ConfigParser()

    if os.path.isfile(filename):
        config.read(filename)
        return config
    else:
        return None


def run_bot():
    """"""
    # Get config from file
    config_file = 'config.ini'
    config = get_config(config_file)

    if config is None:
        sys.exit(f'Could not find "{config_file}" config file. Check the README for instructions on creating a config.')

    # Get database object
    loop = asyncio.get_event_loop()
    db = loop.run_until_complete(get_db(**config['PostgreSQL Database']))

    # Instantiate bot and run
    dbl_token = config.get('DBL API', 'dbl_token', fallback=None)
    bot = LeagueBot(**config['Discord API'], **config['CS:GO League API'], db=db, dbl_token=dbl_token)
    bot.run()


if __name__ == '__main__':
    run_bot()
