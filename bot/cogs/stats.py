# stats.py

from discord.ext import commands
import math

from .utils import PlayerStats


def align_text(text, length, align='center'):
    """ Center the text within whitespace of input length. """
    if length < len(text):
        return text

    whitespace = length - len(text)

    if align == 'center':
        pre = math.floor(whitespace / 2)
        post = math.ceil(whitespace / 2)
    elif align == 'left':
        pre = 0
        post = whitespace
    elif align == 'right':
        pre = whitespace
        post = 0
    else:
        raise ValueError('Align argument must be "center", "left" or "right"')

    return ' ' * pre + text + ' ' * post


class StatsCog(commands.Cog):
    """ Cog to manage stat-related functionality. """

    def __init__(self, bot):
        """ Set attributes. """
        self.bot = bot

    @commands.command(brief='See your stats')
    async def stats(self, ctx):
        """ Send an embed containing stats data parsed from the player object returned from the API. """

        try:
            user = ctx.message.mentions[0]
        except IndexError:
            user = ctx.author

        stats = await PlayerStats.from_user(user)

        if stats:
            win_percent_str = f'{stats.win_percent * 100:.2f}%'
            hs_percent_str = f'{stats.hs_percent * 100:.2f}%'
            fb_percent_str = f'{stats.first_blood_rate * 100:.2f}%'
            description = '```ml\n' \
                          f' RankMe Score:      {stats.score:>6} \n' \
                          f' Matches Played:    {stats.matches_played:>6} \n' \
                          f' Win Percentage:    {win_percent_str:>6} \n' \
                          f' KD Ratio:          {stats.kd_ratio:>6.2f} \n' \
                          f' ADR:               {stats.adr:>6.2f} \n' \
                          f' HS Percentage:     {hs_percent_str:>6} \n' \
                          f' First Blood Rate:  {fb_percent_str:>6} ' \
                          '```'
            embed = self.bot.embed_template(description=description)
            embed.set_author(name=user.display_name, url=stats.league_profile, icon_url=user.avatar_url_as(size=128))
        else:
            title = f'Unable to get **{ctx.author.display_name}**\'s stats: Their account not linked'
            embed = self.bot.embed_template(title=title)

        await ctx.send(embed=embed)

    @commands.command(brief='See the top players in the server')
    async def leaders(self, ctx):
        """ Send an embed containing the leaderboard data parsed from the player objects returned from the API. """
        num = 5  # Easily modfiy the number of players on the leaderboard
        players_stats = [x async for x in PlayerStats.from_users(ctx.guild.members)]

        if not players_stats:
            embed = self.bot.embed_template(title='Nobody on this server is ranked!')
            await ctx.send(embed=embed)
        else:
            players_stats.sort(key=lambda u: (u.score, u.matches_played), reverse=True)

            # Select the top players only
            if len(players_stats) > num:
                players_stats = players_stats[:num]

            # Generate leaderboard text
            data = [['Player'] + ctx._get_members([player.discord for player in players_stats]),
                    ['Score'] + [str(player.score) for player in players_stats],
                    ['Winrate'] + [f'{player.win_percent * 100:.2f}%' for player in players_stats],
                    ['Played'] + [str(player.matches_played) for player in players_stats]]
            data[0] = [data[0][0]] + \
                [member.display_name if len(member.display_name) < 12 else member.display_name[:9] + '...'
                    for member in data[0][1:]]  # Shorten long names
            widths = list(map(lambda x: len(max(x, key=len)), data))
            aligns = ['left', 'right', 'right', 'right']
            z = zip(data, widths, aligns)
            formatted_data = [list(map(lambda x: align_text(x, width, align), col)) for col, width, align in z]
            formatted_data = list(map(list, zip(*formatted_data)))  # Transpose list for .format() string
            description = '```ml\n    {}  {}  {}  {} \n'.format(*formatted_data[0])

            for rank, player_row in enumerate(formatted_data[1:], start=1):
                description += ' {}. {}  {}  {}  {} \n'.format(rank, *player_row)

            description += '```'

            # Send leaderboard
            title = '__CS:GO League Server Leaderboard__'
            embed = self.bot.embed_template(title=title, description=description)
            await ctx.send(embed=embed)
