# auth.py

import asyncio
from discord.ext import commands

from .utils import Player


class AuthCog(commands.Cog):
    """ Cog to manage authorisation. """

    def __init__(self, bot):
        """ Set attributes. """
        self.bot = bot

    @commands.command(brief='Link Discord account to Steam to start playing')
    async def link(self, ctx):
        """ Link a player by sending them a link to sign in with Steam on the backend. """
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

    @commands.command(brief='Unlink Steam account and delete all user data')
    async def unlink(self, ctx):
        """ Unlink a player on the backend and delete their stored data. """
        timeout = 15
        check_mark = '✅'
        embed = self.bot.embed_template(title='Are you sure you want to unlink your account?', description='**Your Steam account link and all stored data (rank, matches, stats) will be deleted**')
        embed.set_footer(text=f'Click the {check_mark} within the next {timeout} seconds to confirm')
        msg = await ctx.send(embed=embed)
        await msg.add_reaction(check_mark)

        try:
            await self.bot.wait_for('reaction_add', timeout=timeout, check=lambda r, u: u == ctx.author)
        except asyncio.TimeoutError:  # Sender didn't react
            embed.description = '*Account preserved*'
        else:
            await Player(ctx.author.id).unlink()
            embed.description = '*Account unlinked and deleted*'

        embed.set_footer()
        await msg.edit(embed=embed)
        await msg.clear_reactions()
