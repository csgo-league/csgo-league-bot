# leaguebot.py

import discord
from discord.ext import commands

import logging
import os.path
import sys
import traceback
import json

from aiohttp import ClientSession

from . import cogs
from .resources import Sessions, Config

_CWD = os.path.dirname(os.path.abspath(__file__))
INTENTS_JSON = os.path.join(_CWD, 'intents.json')


class LeagueBot(commands.AutoShardedBot):
    """ Sub-classed AutoShardedBot modified to fit the needs of the application. """

    def __init__(self, discord_token, api_base_url, api_key, db_pool, emoji_dict, donate_url=None):
        """ Set attributes and configure bot. """
        # Call parent init
        with open(INTENTS_JSON) as f:
            intents_attrs = json.load(f)

        intents = discord.Intents(**intents_attrs)
        super().__init__(command_prefix=('q!', 'Q!'), case_insensitive=True, intents=intents)

        # Set argument attributes
        self.discord_token = discord_token
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.db_pool = db_pool
        self.emoji_dict = emoji_dict
        self.donate_url = donate_url

        # Set constants
        self.description = 'An easy to use, fully automated system to set up and play CS:GO pickup games'
        self.color = 0x000000
        self.activity = discord.Activity(type=discord.ActivityType.watching, name="noobs type q!help")  # TODO: Make help command string dynamic
        self.logger = logging.getLogger('csgoleague.bot')

        Config.api_url = self.api_base_url

        if not self.api_base_url.startswith('https') \
                and self.api_base_url.startswith('http'):

            self.logger.warning(
                f'API url "{self.api_base_url}" should start with "https" instead of "http"'
            )

        # Add check to not respond to DM'd commands
        self.add_check(lambda ctx: ctx.guild is not None)

        # Trigger typing before every command
        self.before_invoke(commands.Context.trigger_typing)

        # Add cogs
        self.add_cog(cogs.LoggingCog(self))
        self.add_cog(cogs.HelpCog(self))
        self.add_cog(cogs.AuthCog(self))
        self.add_cog(cogs.QueueCog(self))
        self.add_cog(cogs.MatchCog(self))
        self.add_cog(cogs.StatsCog(self))

        if self.donate_url:
            self.add_cog(cogs.DonateCog(self))

    async def get_context(self, message, *, cls=None):
        """ Override parent method to use LeagueContext """
        return await super().get_context(message, cls=cls or cogs.utils.LeagueContext)

    async def on_error(self, event_method, *args, **kwargs):
        """"""
        try:
            logging_cog = self.get_cog('LoggingCog')

            if logging_cog is None:
                super().on_error(event_method, *args, **kwargs)
            else:
                exc_type, exc_value, traceback = sys.exc_info()
                logging_cog.log_exception(f'Uncaught exception when handling "{event_method}" event:', exc_value)
        except Exception as e:
            print(e)

    def get_users(self, user_ids):
        """"""
        return [self.get_user(uid) for uid in user_ids]

    def embed_template(self, **kwargs):
        """ Implement the bot's default-style embed. """
        kwargs['color'] = self.color
        return discord.Embed(**kwargs)

    @commands.Cog.listener()
    async def on_connect(self):
        Sessions.requests = ClientSession(
            loop=self.loop,
            headers={"authentication": self.api_key},
            json_serialize=lambda x: json.dumps(x, ensure_ascii=False),
            raise_for_status=True,
            trace_configs=[cogs.TRACE_CONFIG]
        )

    @commands.Cog.listener()
    async def on_ready(self):
        """ Synchronize the guilds the bot is in with the guilds table. """
        async with self.db_pool.acquire() as conn:
            db = cogs.utils.DBHelper(conn)
            await db.sync_guilds(*(guild.id for guild in self.guilds))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """ Insert the newly added guild to the guilds table. """
        async with self.db_pool.acquire() as conn:
            db = cogs.utils.DBHelper(conn)
            await db.insert_guilds(guild.id)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """ Delete the recently removed guild from the guilds table. """
        async with self.db_pool.acquire() as conn:
            db = cogs.utils.DBHelper(conn)
            await db.delete_guilds(guild.id)

    def run(self):
        """ Override parent run to automatically include Discord token. """
        super().run(self.discord_token)

    async def close(self):
        """ Override parent close to close the API session and DB connection pool. """
        await super().close()
        await self.db_pool.close()

        self.logger.info('Closing API helper client session')
        await Sessions.requests.close()
