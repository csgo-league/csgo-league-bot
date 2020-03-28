# auth.py

import discord
from discord.ext import commands


class PopflashCog(commands.Cog):
    """ Cog to manage authorisation. """

    def __init__(self, bot, color):
        """ Set attributes. """
        self.bot = bot
        self.color = color

    async def cog_before_invoke(self, ctx):
        """ Trigger typing at the start of every command. """
        await ctx.trigger_typing()

    @commands.command(brief='Link a player on the backend')
    async def link(self, ctx):
        """ Link a player by sending them a link to sign in with steam on the backend. """

        if apiHelper.is_linked(ctx.author.id) == True:
            title = f'Unable to link **{ctx.author.display_name}**: They are already linked'
        else:
            response = apiHelper.generate_code(ctx.author.id)
            response = response.json()

            code,error = response

            if code:
                # Send the author a DM containing this link
                link = f'{BASE_URL}/discord/{ctx.author.id}/{code}'
            elif error:
                # Tell them that there was a freak error \o/


        embed = discord.Embed(title=title, color=self.color)
        await ctx.send(embed=embed)
