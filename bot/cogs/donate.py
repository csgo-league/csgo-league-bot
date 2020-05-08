# donate.py

from discord.ext import commands


class DonateCog(commands.Cog):
    """ Cog to manage interactions with donate links. """

    def __init__(self, bot):
        """ Set attributes """
        self.bot = bot

    @commands.command(brief='Link the bot\'s donation link')
    async def donate(self, ctx):
        description = f'[Click here to donate]({self.bot.donate_url})'
        embed = self.bot.embed_template(title="Donations are greatly appreciated!", description=description)
        await ctx.send(embed=embed)
