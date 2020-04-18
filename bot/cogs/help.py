# help.py

import discord
from discord.ext import commands
import Levenshtein as lev

GITHUB = 'https://github.com/csgo-league/csgo-league-bot'  # TODO: Use git API to get link to repo?
SERVER_INV = 'https://discord.gg/b5MhANU'


class HelpCog(commands.Cog):
    """ Handles everything related to the help menu. """

    def __init__(self, bot):
        """ Set attributes and remove default help command. """
        self.bot = bot
        self.logo = 'https://raw.githubusercontent.com/csgo-league/csgo-league-bot/master/assets/logo/logo.jpg'
        self.bot.remove_command('help')
        self.bot.ignore_error_types.add(commands.CommandNotFound)

    def help_embed(self, title):
        embed = discord.Embed(title=title, color=self.bot.color)
        prefix = self.bot.command_prefix
        prefix = prefix[0] if prefix is not str else prefix

        for cog in self.bot.cogs:  # Uset bot.cogs instead of bot.commands to control ordering in the help embed
            for cmd in self.bot.get_cog(cog).get_commands():
                if cmd.usage:  # Command has usage attribute set
                    embed.add_field(name=f'**{prefix}{cmd.usage}**', value=f'_{cmd.brief}_', inline=False)
                else:
                    embed.add_field(name=f'**{prefix}{cmd.name}**', value=f'_{cmd.brief}_', inline=False)

        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        """ Set presence to let users know the help command. """
        activity = discord.Activity(type=discord.ActivityType.watching, name="noobs type q!help")
        await self.bot.change_presence(activity=activity)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """ Send help message when a mis-entered command is received. """
        if type(error) is commands.CommandNotFound:
            # Get Levenshtein distance from commands
            in_cmd = ctx.invoked_with
            bot_cmds = list(self.bot.commands)
            lev_dists = [lev.distance(in_cmd, str(cmd)) / max(len(in_cmd), len(str(cmd))) for cmd in bot_cmds]
            lev_min = min(lev_dists)

            # Prep help message title
            embed_title = f'**```{ctx.message.content}```** is not valid!'
            prefixes = self.bot.command_prefix
            prefix = prefixes[0] if prefixes is not str else prefixes  # Prefix can be string or iterable of strings

            # Make suggestion if lowest Levenshtein distance is under threshold
            if lev_min <= 0.5:
                embed_title += f' Did you mean `{prefix}{bot_cmds[lev_dists.index(lev_min)]}`?'
            else:
                embed_title += f' Use `{prefix}help` for a list of commands'

            embed = discord.Embed(title=embed_title, color=self.bot.color)
            await ctx.send(embed=embed)

    @commands.command(brief='Display the help menu')  # TODO: Add 'or details of the specified command'
    async def help(self, ctx):
        """ Generate and send help embed based on the bot's commands. """
        embed = self.help_embed('__CS:GO League Bot Commands__')
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """ Send the help embed if the bot is mentioned. """
        if self.bot.user in message.mentions:
            await message.channel.send(embed=self.help_embed('__CS:GO League Bot Commands__'))

    @commands.command(brief='Display basic info about this bot')
    async def about(self, ctx):
        """ Display the info embed. """
        description = '_CS:GO PUGs made easy so you can just play. End-to-end support from Discord to matches._\n'
        description += f'\nJoin the [support server]({SERVER_INV})'
        dbl_cog = self.bot.get_cog('DblCog')

        if dbl_cog:
            description += f'\nBe sure to upvote the bot on [top.gg]({dbl_cog.topgg_url})'

        description += f'\nSource code can be found on [GitHub]({GITHUB})'
        embed = discord.Embed(title='__CS:GO League Bot__', description=description, color=self.bot.color)
        embed.set_thumbnail(url=self.logo)
        await ctx.send(embed=embed)
