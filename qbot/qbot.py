# qbot.py

from discord.ext import commands
from helpers.api import ApiHelper

import cogs
import aiohttp

BOT_COLOR = 0x000000
DATA_PATH = 'guild_data.json'


def run(discord_token, api_base_url, api_key, dbl_token=None, donate_url=None):
    """ Create the bot, add the cogs and run it. """
    bot = commands.Bot(command_prefix=('q!', 'Q!'), case_insensitive=True)

    # Can't close aiohttp session cleanly because of current initialization method
    api_helper = ApiHelper(aiohttp.ClientSession(loop=bot.loop), api_base_url, api_key)

    bot.add_cog(cogs.CacherCog(bot, DATA_PATH))
    bot.add_cog(cogs.ConsoleCog(bot))
    bot.add_cog(cogs.HelpCog(bot, BOT_COLOR))
    bot.add_cog(cogs.AuthCog(bot, api_helper, BOT_COLOR))
    bot.add_cog(cogs.QueueCog(bot, api_helper, BOT_COLOR))
    bot.add_cog(cogs.TeamDraftCog(bot, BOT_COLOR))
    bot.add_cog(cogs.MapDraftCog(bot, BOT_COLOR))

    if dbl_token:
        bot.add_cog(cogs.DblCog(bot, dbl_token))

    if donate_url:
        bot.add_cog(cogs.DonateCog(bot, BOT_COLOR, donate_url))

    bot.run(discord_token)
