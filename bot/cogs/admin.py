# admin.py

import discord
from discord.ext import commands


class AdminCog(commands.Cog):
    """ Contains commands that require elevated privlidges in the Discord server. """

    def __init__(self, bot):
        """ Set attributes. """
        self.bot = bot

    @commands.command(usage='remove <user mention>',
                      brief='Remove the mentioned user from the queue (must have server kick perms)')
    @commands.has_permissions(kick_members=True)
    async def remove(self, ctx):
        """ Remove the specified user from the queue. """
        try:
            removee = ctx.message.mentions[0]
        except IndexError:
            embed = self.bot.embed_template(title='Mention a player in the command to remove them')
            await ctx.send(embed=embed)
        else:
            queue_cog = self.bot.get_cog('QueueCog')
            queue = queue_cog.guild_queues[ctx.guild]

            if removee in queue.active:
                queue.active.remove(removee)
                title = f'**{removee.display_name}** has been removed from the queue'
            elif queue.bursted and removee in queue.bursted:
                queue.bursted.remove(removee)

                if len(queue.active) >= 1:
                    # await ctx.trigger_typing()  # Need to retrigger typing for second send
                    saved_queue = queue.active.copy()
                    first_in_queue = saved_queue[0]
                    queue.active = queue.bursted + [first_in_queue]
                    queue.bursted = []
                    burst_embed, user_mentions = queue_cog.burst_queue(ctx.guild)
                    await ctx.send(user_mentions, embed=burst_embed)

                    if len(queue.active) > 1:
                        queue.active = saved_queue[1:]

                    return
                else:
                    queue.active = queue.bursted
                    queue.bursted = []
                    title = f'**{removee.display_name}** has been removed from the most recent filled queue'

            else:
                title = f'**{removee.display_name}** is not in the queue or the most recent filled queue'

            embed = queue_cog.queue_embed(ctx.guild, title)

            if queue.last_msg:
                try:
                    await queue.last_msg.delete()
                except discord.errors.NotFound:
                    pass

            queue.last_msg = await ctx.send(embed=embed)

    @commands.command(brief='Empty the queue (must have server kick perms)')
    @commands.has_permissions(kick_members=True)
    async def empty(self, ctx):
        """ Reset the guild queue list to empty. """
        queue_cog = self.bot.get_cog('QueueCog')
        queue = queue_cog.guild_queues[ctx.guild]
        queue.active.clear()
        embed = queue_cog.queue_embed(ctx.guild, 'The queue has been emptied')

        if queue.last_msg:
            try:
                await queue.last_msg.delete()
            except discord.errors.NotFound:
                pass

        queue.last_msg = await ctx.send(embed=embed)

    @remove.error
    @empty.error
    async def remove_error(self, ctx, error):
        """ Respond to a permissions error with an explanation message. """
        if isinstance(error, commands.MissingPermissions):
            await ctx.trigger_typing()
            missing_perm = error.missing_perms[0].replace('_', ' ')
            title = f'Cannot remove players without {missing_perm} permission!'
            embed = self.bot.embed_template(title=title)
            await ctx.send(embed=embed)

    @commands.command(usage='ban <user mention> ... [hour length]',
                      brief='Ban one or more players from queueing for a certain number of hours or indefinitely')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, *args):
        """ Ban player(s) via the API. """
        try:
            ban_hours = float(args[-1])
        except ValueError:
            ban_hours = None

        if len(ctx.message.mentions) > 0:
            queue_cog = self.bot.get_cog('QueueCog')
            active_queue = queue_cog.guild_queues[ctx.guild].active
            banned_str = ''

            for bannee in ctx.message.mentions:
                if bannee in active_queue:
                    active_queue.remove(bannee)

                await self.bot.api.ban_player(bannee)
                banned_str += f'**{bannee.display_name}**, '

            title = 'Banned ' + banned_str[:-2] + ' from queueing'

            if ban_hours is None:
                title += ' indefinitely'
            else:
                title += f' for {ban_hours:.2f} hours'
        else:
            title = 'Mention a player in the command to ban them'

        embed = self.bot.embed_template(title=title)
        await ctx.send(embed=embed)

    @commands.command(usage='unban <user mention> ...',
                      brief='Unban one or more players so they are allowed to queue')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx):
        """ Unban player(s) via the API. """
        if len(ctx.message.mentions) > 0:
            unbanned_str = ''

            for unbannee in ctx.message.mentions:
                await self.bot.api.unban_player(unbannee)
                unbanned_str += f'**{unbannee.display_name}**, '

            title = 'Unbanned ' + unbanned_str[:-2]
        else:
            title = 'Mention a player in the command to unban them'

        embed = self.bot.embed_template(title=title)
        await ctx.send(embed=embed)

    @ban.error
    @unban.error
    async def ban_error(self, ctx, error):
        """ Respond to a permissions error with an explanation message. """
        if isinstance(error, commands.MissingPermissions):
            await ctx.trigger_typing()
            missing_perm = error.missing_perms[0].replace('_', ' ')
            title = f'Cannot {ctx.command.name} players without {missing_perm} permission!'
            embed = self.bot.embed_template(title=title)
            await ctx.send(embed=embed)

    @commands.command(brief='Set the capacity of the queue (Must have admin perms)')
    @commands.has_permissions(administrator=True)
    async def cap(self, ctx, *args):
        """ Set the queue capacity. """
        queue = self.guild_queues[ctx.guild]

        if len(args) == 0:  # No size argument specified
            embed = self.bot.embed_template(title=f'The current queue capacity is {queue.capacity}')
        else:
            new_cap = args[0]

            try:
                new_cap = int(new_cap)
            except ValueError:
                embed = self.bot.embed_template(title=f'{new_cap} is not an integer')
            else:
                if new_cap < 2 or new_cap > 100:
                    embed = self.bot.embed_template(title='Capacity is outside of valid range')
                else:
                    queue.active.clear()  # Empty active queue to prevent bugs related to capacity size
                    queue.capacity = new_cap
                    embed = self.bot.embed_template(title=f'Queue capacity set to {new_cap}')
                    embed.set_footer(text='The queue has been emptied because of the capacity change')

        await ctx.send(embed=embed)

    @cap.error
    async def cap_error(self, ctx, error):
        """ Respond to a permissions error with an explanation message. """
        if isinstance(error, commands.MissingPermissions):
            await ctx.trigger_typing()
            missing_perm = error.missing_perms[0].replace('_', ' ')
            title = f'Cannot change queue capacity without {missing_perm} permission!'
            embed = self.bot.embed_template(title=title)
            await ctx.send(embed=embed)
