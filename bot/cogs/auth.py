# auth.py

from discord.ext import commands

from .utils import Player


class AuthCog(commands.Cog):
    """ Cog to manage authorisation. """

    def __init__(self, bot):
        """ Set attributes. """
        self.bot = bot

    @commands.command(brief='Link a player on the backend')
    async def link(self, ctx):
        """ Link a player by sending them a link to sign in with steam on the backend. """
        player = Player(ctx.author.id)

        if await player.is_linked():
            title = f'Unable to link **{ctx.author.display_name}**: They are already linked'
        else:
            link = await player.generate_link_url()

            if link:
                # Send the author a DM containing this link
                await ctx.author.send(f'Click this URL to authorize CS:GO League to verify your Steam account\n{link}')
                title = f'Link URL sent to **{ctx.author.display_name}**'
            else:
                title = f'Unable to link **{ctx.author.display_name}**: Unknown error'

        embed = self.bot.embed_template(title=title)
        await ctx.send(embed=embed)
