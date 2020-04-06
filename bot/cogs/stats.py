# stats.py

import discord
from discord.ext import commands


class StatsCog(commands.Cog):
    """ Cog to manage stat-related functionality. """

    def __init__(self, bot):
        """ Set attributes. """
        self.bot = bot

    async def cog_before_invoke(self, ctx):
        """ Trigger typing at the start of every command. """
        await ctx.trigger_typing()

    @commands.command(brief='See your stats')
    async def stats(self, ctx):
        """ Send an embed containing stats data parsed from the player object returned from the API. """
        user = ctx.author
        player = await self.bot.api_helper.get_player(user)

        if player:
            win_percent_str = f'{player.win_percent * 100:.2f}%'
            hs_percent_str = f'{player.hs_percent * 100:.2f}%'
            fb_percent_str = f'{player.first_blood_rate * 100:.2f}%'
            description = '```ml\n' \
                          f'     RankMe Score: {player.score:<7}\n' \
                          f'   Matches Played: {player.matches_played:<7}\n' \
                          f'   Win Percentage: {win_percent_str:<7}\n' \
                          f'         KD Ratio: {player.kd_ratio:<7.2f}\n' \
                          f'              ADR: {player.adr:<7.2f}\n' \
                          f'    HS Percentage: {hs_percent_str:<7}\n' \
                          f' First Blood Rate: {fb_percent_str:<7}' \
                          '```'
            embed = discord.Embed(title='__CS:GO League Stats__', description=description, color=self.bot.color)
            embed.set_author(name=user.display_name, url=player.steam_profile, icon_url=user.avatar_url_as(size=128))
        else:
            title = f'Unable to get **{ctx.author.display_name}**\'s stats: Their account not linked'
            embed = discord.Embed(title=title, color=self.bot.color)

        await ctx.send(embed=embed)
