# queue.py

from discord.ext import commands
import discord
import asyncio
from datetime import datetime, timedelta, timezone
import re

from .utils import Player


class QueueCog(commands.Cog):
    """ Cog to manage queues of players among multiple servers. """

    time_arg_pattern = re.compile(r'\b((?:(?P<days>[0-9]+)d)|(?:(?P<hours>[0-9]+)h)|(?:(?P<minutes>[0-9]+)m))\b')

    def __init__(self, bot):
        """ Set attributes. """
        self.bot = bot
        self.last_queue_msgs = {}

    async def queue_embed(self, ctx, title=None):
        """ Method to create the queue embed for a guild. """
        queued_users = await ctx.queued_users()
        config = await ctx.guild_config()

        if title:
            title += f' ({len(queued_users)}/{config.capacity})'

        if len(queued_users) == 0:  # If there are no users in the queue
            queue_str = '_The queue is empty..._'
        else:  # Users still in queue
            queue_str = ''.join(f'{num}. {user.mention}\n' for num, user in enumerate(queued_users, start=1))

        embed = self.bot.embed_template(title=title, description=queue_str)
        embed.set_footer(text='Players will receive a notification when the queue fills up')
        return embed

    async def update_last_msg(self, ctx, embed):
        """ Send embed message and delete the last one sent. """
        msg = self.last_queue_msgs.get(ctx.guild)

        if msg is not None:
            try:
                await msg.delete()
            except discord.errors.NotFound:
                pass

        self.last_queue_msgs[ctx.guild] = await ctx.send(embed=embed)

    @commands.command(brief='Join the queue')
    async def join(self, ctx):
        """ Check if the member can be added to the guild queue and add them if so. """

        player = Player(ctx.author)
        if not await player.is_linked():  # Message author isn't linked
            title = f'Unable to add **{ctx.author.display_name}**: Their account is not linked'
        else:  # Message author is linked
            awaitables = [
                player.get_stats(),
                ctx.queued_users(),
                ctx.guild_config(),
                ctx.queue_banlist()
            ]
            results = await asyncio.gather(*awaitables, loop=self.bot.loop)
            player_stats = results[0]
            queued_users = results[1]
            capacity = results[2].capacity
            banned_users = results[3]

            if ctx.author in banned_users:  # Author is banned from joining the queue
                title = f'Unable to add **{ctx.author.display_name}**: Banned'
                unban_time = banned_users[ctx.author]

                if unban_time is not None:  # If the user is banned for a duration
                    title += f' for {self.timedelta_str(unban_time - datetime.now(timezone.utc))}'

            elif ctx.author in queued_users:  # Author already in queue
                title = f'Unable to add **{ctx.author.display_name}**: Already in the queue'
            elif len(queued_users) >= capacity:  # Queue full
                title = f'Unable to add **{ctx.author.display_name}**: Queue is full'
            elif not player_stats:  # Couldn't get player from API TODO: Remove this and raise exception in ApiHelper
                title = f'Unable to add **{ctx.author.display_name}**: Cannot verify match status'
            elif player_stats.in_match:  # User is already in a match
                title = f'Unable to add **{ctx.author.display_name}**: Already in a match'
            else:  # User can be added
                await ctx.enqueue_users(ctx.author)
                queued_users += [ctx.author]
                title = f'**{ctx.author.display_name}** has been added to the queue'

                # Check and burst queue if full
                if len(queued_users) == capacity:
                    match_cog = self.bot.get_cog('MatchCog')

                    try:
                        all_readied = await match_cog.start_match(ctx, queued_users)
                    except asyncio.TimeoutError:
                        return

                    if all_readied:
                        await ctx.empty_queue()

                    return

        embed = await self.queue_embed(ctx, title)

        # Delete last queue message
        await self.update_last_msg(ctx, embed)

    @commands.command(brief='Leave the queue')
    async def leave(self, ctx):
        """ Check if the member can be remobed from the guild and remove them if so. """
        removed = await ctx.dequeue_users(ctx.author)
        name = ctx.author.nick if ctx.author.nick is not None else ctx.author.display_name

        if ctx.author in removed:
            title = f'**{name}** has been removed from the queue'
        else:
            title = f'**{name}** isn\'t in the queue'

        embed = await self.queue_embed(ctx, title)

        # Update queue display message
        await self.update_last_msg(ctx, embed)

    @commands.command(brief='Display who is currently in the queue')
    async def view(self, ctx):
        """ Display the queue as an embed list of mentioned names. """
        title = 'Players in queue for PUGs'
        embed = await self.queue_embed(ctx, title)

        # Update queue display message
        await self.update_last_msg(ctx, embed)

    @commands.command(usage='remove <user mention>',
                      brief='Remove the mentioned user from the queue (need server kick perms)')
    @commands.has_permissions(kick_members=True)
    async def remove(self, ctx):
        """ Remove the specified user from the queue. """
        try:
            removee = ctx.message.mentions[0]
        except IndexError:
            embed = self.bot.embed_template(title='Mention a user in the command to remove them')
            await ctx.send(embed=embed)
        else:
            removed = await ctx.dequeue_users(removee)
            name = removee.nick if removee.nick is not None else removee.display_name

            if removee in removed:
                title = f'**{name}** has been removed from the queue'
            else:
                title = f'**{name}** is not in the queue'

            embed = await self.queue_embed(ctx, title)

            # Update queue display message
            await self.update_last_msg(ctx, embed)

    @commands.command(brief='Empty the queue (need server kick perms)')
    @commands.has_permissions(kick_members=True)
    async def empty(self, ctx):
        """ Reset the guild queue list to empty. """
        await ctx.empty_queue()
        embed = await self.queue_embed(ctx, 'The queue has been emptied')

        # Update queue display message
        await self.update_last_msg(ctx, embed)

    @remove.error
    @empty.error
    async def remove_error(self, ctx, error):
        """ Respond to a permissions error with an explanation message. """
        if isinstance(error, commands.MissingPermissions):
            await ctx.trigger_typing()
            missing_perm = error.missing_perms[0].replace('_', ' ')
            embed = self.bot.embed_template(title=f'Cannot remove players without {missing_perm} permission!')
            await ctx.send(embed=embed)

    @commands.command(usage='cap [<new capacity>]',
                      brief='Set or view the capacity of the queue (need admin perms)')
    @commands.has_permissions(administrator=True)
    async def cap(self, ctx, *args):
        """ Set the queue capacity. """
        config = await ctx.guild_config()
        capacity = config.capacity
        lower_bound = 2
        upper_bound = 100

        if len(args) == 0:  # No size argument specified
            embed = self.bot.embed_template(title=f'The current queue capacity is {capacity}')
        else:
            new_cap = args[0]

            try:
                new_cap = int(new_cap)
            except ValueError:
                embed = self.bot.embed_template(title=f'{new_cap} is not an integer')
            else:
                if new_cap == capacity:
                    embed = self.bot.embed_template(title=f'Capacity is already set to {capacity}')
                elif new_cap < lower_bound or new_cap > upper_bound:
                    title = f'Capacity is outside of valid range ({lower_bound}-{upper_bound})'
                    embed = self.bot.embed_template(title=title)
                else:
                    await ctx.empty_queue()
                    await ctx.set_guild_config(capacity=new_cap)
                    embed = self.bot.embed_template(title=f'Queue capacity set to {new_cap}')
                    embed.set_footer(text='The queue has been emptied because of the capacity change')

        await ctx.send(embed=embed)

    @cap.error
    async def cap_error(self, ctx, error):
        """ Respond to a permissions error with an explanation message. """
        if isinstance(error, commands.MissingPermissions):
            await ctx.trigger_typing()
            missing_perm = error.missing_perms[0].replace('_', ' ')
            embed = self.bot.embed_template(title=f'Cannot change queue capacity without {missing_perm} permission!')
            await ctx.send(embed=embed)

    @staticmethod
    def timedelta_str(tdelta):
        """ Convert time delta object to a worded string representation with only days, hours and minutes. """
        conversions = (('days', 86400), ('hours', 3600), ('minutes', 60))
        secs_left = int(tdelta.total_seconds())
        unit_strings = []

        for unit, conversion in conversions:
            unit_val, secs_left = divmod(secs_left, conversion)

            if unit_val != 0 or (unit == 'minutes' and len(unit_strings) == 0):
                unit_strings.append(f'{unit_val} {unit}')

        return ', '.join(unit_strings)

    @commands.command(usage='ban <user mention> ... [<days>d] [<hours>h] [<minutes>m]',
                      brief='Ban all mentioned users from joining the queue (need server ban perms)')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, *args):
        """ Ban users mentioned in the command from joining the queue for a certain amount of time or indefinitely. """
        # Check that users are mentioned
        if len(ctx.message.mentions) == 0:
            embed = self.bot.embed_template(title='Mention a user in the command to ban them')
            await ctx.send(embed=embed)
            return

        # Parse the time arguments
        time_units = ('days', 'hours', 'minutes')
        time_delta_values = {}  # Holds the values for each time unit arg

        for match in self.time_arg_pattern.finditer(ctx.message.content):  # Iterate over the time argument matches
            for time_unit in time_units:  # Figure out which time unit this match is for
                time_value = match.group(time_unit)  # Get the value for this unit

                if time_value is not None:  # Check if there is an actual group value
                    time_delta_values[time_unit] = int(time_value)
                    break  # There is only ever one group value per match

        # Set unban time if there were time arguments
        time_delta = timedelta(**time_delta_values)
        unban_time = None if time_delta_values == {} else datetime.now(timezone.utc) + time_delta

        # Insert mentions into ban table
        await ctx.ban_from_queue(*ctx.message.mentions, unban_time=unban_time)

        # Remove banned users from the queue
        await ctx.dequeue_users(*ctx.message.mentions)

        # Generate embed and send message
        banned_users_str = ', '.join(f'**{user.display_name}**' for user in ctx.message.mentions)
        ban_time_str = '' if unban_time is None else f' for {self.timedelta_str(time_delta)}'
        embed = self.bot.embed_template(title=f'Banned {banned_users_str}{ban_time_str}')
        embed.set_footer(text='Banned users have been removed from the queue')
        await ctx.send(embed=embed)

    @commands.command(usage='unban <user mention> ...',
                      brief='Unban all mentioned users so they can join the queue (need server ban perms)')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx):
        """ Unban users mentioned in the command so they can join the queue. """
        # Check that users are mentioned
        if len(ctx.message.mentions) == 0:
            embed = self.bot.embed_template(title='Mention a user in the command to unban them')
            await ctx.send(embed=embed)
            return

        # Delete users from the ban table
        unbanned_users = await ctx.unban_from_queue(*ctx.message.mentions)

        # Generate embed and send message
        never_banned_users = [user for user in ctx.message.mentions if user not in unbanned_users]
        unbanned_users_str = ', '.join(f'**{user.display_name}**' for user in unbanned_users)
        never_banned_users_str = ', '.join(f'**{user.display_name}**' for user in never_banned_users)
        title_1 = 'nobody' if unbanned_users_str == '' else unbanned_users_str
        were_or_was = 'were' if len(never_banned_users) > 1 else 'was'
        title_2 = '' if never_banned_users_str == '' else f' ({never_banned_users_str} {were_or_was} never banned)'
        embed = self.bot.embed_template(title=f'Unbanned {title_1}{title_2}')
        embed.set_footer(text='Unbanned users may now join the queue')
        await ctx.send(embed=embed)
