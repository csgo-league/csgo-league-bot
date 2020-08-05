# console.py

import __main__
from discord.ext import commands
import logging
from logging import config
from os import path


LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'defaultNoDate': {
            'format': '[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
            'datefmt': '%H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'defaultNoDate',
            'level': 'INFO',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'default',
            'level': 'DEBUG',
            'filename': path.join(path.dirname(path.abspath(__main__.__file__)), 'bot.log'),
            'maxBytes': 7340032,
            'encoding': 'utf-8'
        }
    },
    'loggers': {
        'csgoleague': {
            'level': 'DEBUG'
        },
        'discord.client': {
            'level': 'INFO'
        },
        'discord.gateway': {
            'level': 'WARNING'
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': [
            'console',
            'file'
        ]
    }
}

config.dictConfig(LOGGING_CONFIG)


def log_lines(lvl, msg, *args, sub_lines=None, **kwargs):
    """"""
    if sub_lines is not None:
        longest_subl_pref = len(max(sub_lines.keys(), key=len))

        for prefix, suffix in sub_lines.items():
            msg += '\n    {:<{width}} {}'.format(prefix + ':', suffix, width=longest_subl_pref + 1)

    logging.getLogger('csgoleague.bot').log(lvl, msg, *args, **kwargs)


class LoggingCog(commands.Cog):
    """ Does the console printing of the bot. """

    def __init__(self, bot):
        """ Set bot attribute. """
        self.bot = bot
        self.logger = logging.getLogger('csgoleague.bot')

    @commands.Cog.listener()
    async def on_connect(self):
        lines_dict = {'Username': self.bot.user.name, 'ID': self.bot.user.id}
        log_lines(logging.INFO, 'Connected to Discord', sub_lines=lines_dict)

    @commands.Cog.listener()
    async def on_disconnect(self):
        log_lines(logging.INFO, 'Disconnected from Discord')

    @commands.Cog.listener()
    async def on_resumed(self):
        lines_dict = {'Username': self.bot.user.name, 'ID': self.bot.user.id}
        log_lines(logging.INFO, 'Resumed session with Discord', sub_lines=lines_dict)

    @commands.Cog.listener()
    async def on_ready(self):
        log_lines(logging.INFO, 'Bot is ready to use in %s Discord servers', len(self.bot.guilds))

    @commands.Cog.listener()
    async def on_command(self, ctx):
        lines_dict = {'Caller': f'{ctx.author} ({ctx.author.id})', 'Guild': f'{ctx.guild} ({ctx.guild.id})'}
        log_lines(logging.INFO, 'Command "%s" issued', ctx.command, sub_lines=lines_dict)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        log_lines(logging.INFO, 'Bot has been added to server "%s" (%s)', guild.name, guild.id)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        log_lines(logging.INFO, 'Bot has been removed from server "%s" (%s)', guild.name, guild.id)
