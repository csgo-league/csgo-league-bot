# launcher.py

from bot.bot import LeagueBot

import argparse
import asyncio
import asyncpg
import discord
from dotenv import load_dotenv
import json
import os

EMOJI_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emojis.json')
load_dotenv()  # Load the environment variables in the local .env file


def run_bot():
    """ Parse the config file and run the bot. """
    # Get database object for bot
    connect_url = 'postgresql://{POSTGRESQL_USER}:{POSTGRESQL_PASSWORD}@{POSTGRESQL_HOST}/{POSTGRESQL_DB}'
    loop = asyncio.get_event_loop()
    db_pool = loop.run_until_complete(asyncpg.create_pool(connect_url.format(**os.environ)))

    # Get environment variables
    bot_token = os.environ['DISCORD_BOT_TOKEN']
    api_url = os.environ['CSGO_LEAGUE_API_URL']
    api_key = os.environ['CSGO_LEAGUE_API_KEY']

    if api_url.endswith('/'):
        api_url = api_url[:-1]

    try:
        with open(EMOJI_FILE) as f:
            emoji_dict = json.load(f)
    except OSError:
        print('Emoji file not found: Use the "-e" flag with your guild ID to create bot emojis')
    else:
        bot = LeagueBot(bot_token, api_url, api_key, db_pool, emoji_dict)
        bot.run()


def create_emojis(guild_id):
    """"""
    client = discord.Client(loop=asyncio.new_event_loop())

    @client.event
    async def on_ready():
        """"""
        guild = await client.fetch_guild(guild_id)
        icon_dir = 'assets/maps/icons/'
        reason = 'Used by the CS:GO League Bot'
        existing_emojis = {emoji.name: emoji for emoji in guild.emojis}

        if os.path.exists(EMOJI_FILE):
            with open(EMOJI_FILE) as f:
                emoji_dict = json.load(f)
        else:
            emoji_dict = {}

        for item in os.listdir(icon_dir):
            if item.endswith('.png'):
                emoji_name = item.split('.')[0]  # Remove file extension for emoji name

                # Check if emoji already exists and if it was made by this bot
                if emoji_name in existing_emojis:
                    # Emoji user attribute only accessible with fetch_emoji()
                    existing_emoji = await guild.fetch_emoji(existing_emojis[emoji_name].id)

                    if existing_emoji.user == client.user:
                        print(f'Emoji :{existing_emoji.name}: has already been created in the server, updating')
                        emoji_dict[existing_emoji.name] = f'<:{existing_emoji.name}:{existing_emoji.id}>'
                        continue

                # Attempt to create emoji
                try:
                    with open(os.path.join(icon_dir, item), 'rb') as file:
                        new_emoji = await guild.create_custom_emoji(name=emoji_name, image=file.read(), reason=reason)
                except discord.Forbidden:
                    print('Bot does not have permission to create custom emojis in the specified server')
                    break
                except discord.HTTPException as e:
                    print(f'HTTP exception raised when creating emoji for "{item}": {e.text} ({e.code})')
                except Exception as e:
                    print(f'Exception {e} occurred')
                else:
                    print(f'Emoji :{emoji_name}: created successfully')
                    emoji_dict[new_emoji.name] = f'<:{new_emoji.name}:{new_emoji.id}>'

        with open(EMOJI_FILE, 'w+') as f:
            json.dump(emoji_dict, f)

        await client.close()

    # Run the client with the token in the local .env file
    load_dotenv()
    client.run(os.environ['DISCORD_BOT_TOKEN'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the CS:GO League bot')
    parser.add_argument('-e', '--emojis', type=int, required=False, metavar='serverID',
                        help='create necessary bot emojis in the specified server and save the info to a JSON file')
    args = parser.parse_args()

    if args.emojis:
        guild_id = args.emojis
        create_emojis(guild_id)

    run_bot()
