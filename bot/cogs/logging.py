# console.py

import __main__
from discord.ext import commands
import logging
from logging import handlers
from os import path
import sys

LOGFILE = path.join(path.dirname(path.abspath(__main__.__file__)), 'bot.log')  # Log file in root directory


def format_dec(log_func):
    """"""
    def log_formatted(*args, **kwargs):
        """"""
        msg = args[1]
        sub_lines = kwargs.get('sub_lines', None)

        if sub_lines is not None:
            longest_subl_pref = len(max(sub_lines.keys(), key=len))

            for prefix, suffix in sub_lines.items():
                msg += '\n    {:<{width}} {}'.format(prefix + ':', suffix, width=longest_subl_pref + 1)

        new_args = list(args)
        new_args[1] = msg
        log_func(*new_args, **kwargs)

    return log_formatted


class LoggingCog(commands.Cog):
    """ Does the console printing of the bot. """

    def __init__(self, bot):
        """ Set bot attribute. """
        self.bot = bot

        # Get logger
        logger = logging.getLogger('csgoleague')
        logger.setLevel(logging.INFO)

        # Add stdout handler
        base_fmt_str = '[{asctime}][{levelname}]: {message}'
        sformatter = logging.Formatter(fmt=base_fmt_str, datefmt='%H:%M:%S', style='{')
        shandler = logging.StreamHandler(sys.stdout)
        shandler.setFormatter(sformatter)
        logger.addHandler(shandler)

        # Add rotating file handler
        fformatter = logging.Formatter(fmt=base_fmt_str, datefmt='%Y-%m-%d %H:%M:%S', style='{')
        fhandler = handlers.RotatingFileHandler(LOGFILE, maxBytes=7340032, encoding='utf-8')  # 7MB size
        fhandler.setFormatter(fformatter)
        logger.addHandler(fhandler)

        self.logger = logger

    @format_dec
    def debug(self, msg, sub_lines=None):
        self.logger.debug(msg)

    @format_dec
    def info(self, msg, sub_lines=None):
        self.logger.info(msg)

    @format_dec
    def warning(self, msg, sub_lines=None):
        self.logger.warning(msg)

    @format_dec
    def error(self, msg, sub_lines=None):
        self.logger.error(msg)

    @format_dec
    def critical(self, msg, sub_lines=None):
        self.logger.critical(msg)

    @commands.Cog.listener()
    async def on_connect(self):
        lines_dict = {'Username': self.bot.user.name, 'ID': self.bot.user.id}
        self.info('Connected to Discord', sub_lines=lines_dict)

    @commands.Cog.listener()
    async def on_disconnect(self):
        self.info('Disconnected from Discord')

    @commands.Cog.listener()
    async def on_resumed(self):
        lines_dict = {'Username': self.bot.user.name, 'ID': self.bot.user.id}
        self.info('Resumed session with Discord', sub_lines=lines_dict)

    @commands.Cog.listener()
    async def on_ready(self):
        self.info(f'Bot is ready to use in {len(self.bot.guilds)} Discord servers')

    @commands.Cog.listener()
    async def on_command(self, ctx):
        lines_dict = {'Caller': f'{ctx.author} ({ctx.author.id})', 'Guild': f'{ctx.guild} ({ctx.guild.id})'}
        self.info(f'Command "{ctx.command}" issued', sub_lines=lines_dict)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.info('Bot has been added to server "{guild.name}" ({guild.id})')

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.info('Bot has been removed from server "{guild.name}" ({guild.id})')
