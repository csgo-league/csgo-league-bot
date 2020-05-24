# leaguebot.py

import discord
from discord.ext import commands

from . import cogs
from . import helpers

import aiohttp
import sys
import traceback


class LeagueBot(commands.AutoShardedBot):
    """ Sub-classed AutoShardedBot modified to fit the needs of the application. """

    def __init__(self, discord_token, api_base_url, api_key, db_pool, donate_url=None):
        """ Set attributes and configure bot. """
        # Call parent init
        super().__init__(command_prefix=('q!', 'Q!'), case_insensitive=True)

        # Set argument attributes
        self.discord_token = discord_token
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.db_pool = db_pool
        self.donate_url = donate_url

        # Set constants
        self.description = 'An easy to use, fully automated system to set up and play CS:GO pickup games'
        self.color = 0x000000
        self.activity = discord.Activity(type=discord.ActivityType.watching, name="noobs type q!help")
        self.guild_data_file = 'guild_data.json'

        # Create session for API
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.api_helper = helpers.ApiHelper(self.session, self.api_base_url, self.api_key)

        # Create DB helper to use connection pool
        self.db_helper = helpers.DBHelper(self.db_pool)

        # Initialize set of errors to ignore
        self.ignore_error_types = set()

        # Add check to not respond to DM'd commands
        self.add_check(lambda ctx: ctx.guild is not None)
        self.ignore_error_types.add(commands.errors.CheckFailure)

        # Trigger typing before every command
        self.before_invoke(commands.Context.trigger_typing)

        # Add cogs
        self.add_cog(cogs.ConsoleCog(self))
        self.add_cog(cogs.HelpCog(self))
        self.add_cog(cogs.AuthCog(self))
        self.add_cog(cogs.QueueCog(self))
        self.add_cog(cogs.MatchCog(self))
        # self.add_cog(cogs.MapDraftCog(self))  # Map drafting done in-game for now
        self.add_cog(cogs.StatsCog(self))

        if self.donate_url:
            self.add_cog(cogs.DonateCog(self))

    def embed_template(self, **kwargs):
        """ Implement the bot's default-style embed. """
        kwargs['color'] = self.color
        return discord.Embed(**kwargs)

    @commands.Cog.listener()
    async def on_ready(self):
        """ Synchronize the guilds the bot is in with the guilds table. """
        await self.db_helper.sync_guilds(*(guild.id for guild in self.guilds))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """ Insert the newly added guild to the guilds table. """
        await self.db_helper.insert_guilds(guild.id)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """ Delete the recently removed guild from the guilds table. """
        await self.db_helper.delete_guilds(guild.id)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """ Send help message when a mis-entered command is received. """
        if type(error) not in self.ignore_error_types:
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def run(self):
        """ Override parent run to automatically include Discord token. """
        super().run(self.discord_token)

    async def close(self):
        """ Override parent close to close the API session also. """
        await super().close()
        await self.session.close()
        await self.db_pool.close()
