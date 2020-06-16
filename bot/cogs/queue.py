# queue.py

from discord.ext import commands
import asyncio
from datetime import datetime, timedelta, timezone
import re


class QueueCog(commands.Cog):
    """ Cog to manage queues of players among multiple servers. """

    time_arg_pattern = re.compile(r'\b((?:(?P<days>[0-9]+)d)|(?:(?P<hours>[0-9]+)h)|(?:(?P<minutes>[0-9]+)m))\b')

    def __init__(self, bot):
        """ Set attributes. """
        self.bot = bot
        self.last_queue_msgs = {}

    async def queue_embed(self, guild, title=None):
        """ Method to create the queue embed for a guild. """
        queued_ids = await self.bot.db_helper.get_queued_users(guild.id)
        guild_data = await self.bot.db_helper.get_guild(guild.id)
        capacity = guild_data['capacity']

        if title:
            title += f' ({len(queued_ids)}/{capacity})'

        if len(queued_ids) == 0:  # If there are no users in the queue
            queue_str = '_The queue is empty..._'
        else:  # Users still in queue
            queue_str = ''.join(f'{num}. <@{user_id}>\n' for num, user_id in enumerate(queued_ids, start=1))

        embed = self.bot.embed_template(title=title, description=queue_str)
        embed.set_footer(text='Players will receive a notification when the queue fills up')
        return embed

    async def update_last_msg(self, ctx, embed):
        """ Send embed message and delete the last one sent. """
        msg = self.last_queue_msgs.get(ctx.guild)

        if msg is not None:
            await msg.delete()

        self.last_queue_msgs[ctx.guild] = await ctx.send(embed=embed)

    @commands.command(brief='Join the queue')
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)  # Only process one command per guild at once
    async def join(self, ctx):
        """ Check if the member can be added to the guild queue and add them if so. """
        if not await self.bot.api_helper.is_linked(ctx.author.id):  # Message author isn't linked
            title = f'Unable to add **{ctx.author.display_name}**: Their account is not linked'
        else:  # Message author is linked
            awaitables = [
                self.bot.api_helper.get_player(ctx.author.id),
                self.bot.db_helper.insert_users(ctx.author.id),
                self.bot.db_helper.get_queued_users(ctx.guild.id),
                self.bot.db_helper.get_guild(ctx.guild.id),
                self.bot.db_helper.get_banned_users(ctx.guild.id)
            ]
            results = await asyncio.gather(*awaitables, loop=self.bot.loop)
            player = results[0]
            queue_ids = results[2]
            capacity = results[3]['capacity']
            banned_users = results[4]

            if ctx.author.id in banned_users:  # Author is banned from joining the queue
                title = f'Unable to add **{ctx.author.display_name}**: Banned'
                unban_time = banned_users[ctx.author.id]

                if unban_time is not None:  # If the user is banned for a duration
                    title += f' for {self.timedelta_str(unban_time - datetime.now(timezone.utc))}'

            elif ctx.author.id in queue_ids:  # Author already in queue
                title = f'Unable to add **{ctx.author.display_name}**: Already in the queue'
            elif len(queue_ids) >= capacity:  # Queue full
                title = f'Unable to add **{ctx.author.display_name}**: Queue is full'
            elif not player:  # ApiHelper couldn't get player
                title = f'Unable to add **{ctx.author.display_name}**: Cannot verify match status'
            elif player.in_match:  # User is already in a match
                title = f'Unable to add **{ctx.author.display_name}**: Already in a match'
            else:  # User can be added
                await self.bot.db_helper.insert_queued_users(ctx.guild.id, ctx.author.id)
                queue_ids += [ctx.author.id]
                title = f'**{ctx.author.display_name}** has been added to the queue'

                # Check and burst queue if full
                if len(queue_ids) == capacity:
                    queue_users = [self.bot.get_user(user_id) for user_id in queue_ids]
                    match_cog = self.bot.get_cog('MatchCog')

                    try:
                        all_readied = await match_cog.start_match(ctx, queue_users)
                    except asyncio.TimeoutError:
                        return

                    if all_readied:
                        await self.bot.db_helper.delete_queued_users(ctx.guild.id, *queue_ids)

                    return

        embed = await self.queue_embed(ctx.guild, title)

        # Delete last queue message
        await self.update_last_msg(ctx, embed)

    @commands.command(brief='Leave the queue (or the bursted queue)')
    async def leave(self, ctx):
        """ Check if the member can be remobed from the guild and remove them if so. """
        removed = await self.bot.db_helper.delete_queued_users(ctx.guild.id, ctx.author.id)
        name = ctx.author.nick if ctx.author.nick is not None else ctx.author.display_name

        if ctx.author.id in removed:
            title = f'**{name}** has been removed from the queue'
        else:
            title = f'**{name}** isn\'t in the queue'

        embed = await self.queue_embed(ctx.guild, title)

        # Update queue display message
        await self.update_last_msg(ctx, embed)

    @commands.command(brief='Display who is currently in the queue')
    async def view(self, ctx):
        """ Display the queue as an embed list of mentioned names. """
        title = 'Players in queue for 10-mans'
        embed = await self.queue_embed(ctx.guild, title)

        # Update queue display message
        await self.update_last_msg(ctx, embed)

    @commands.command(usage='remove <user mention>',
                      brief='Remove the mentioned user from the queue (must have server kick perms)')
    @commands.has_permissions(kick_members=True)
    async def remove(self, ctx):
        """ Remove the specified user from the queue. """
        try:
            removee = ctx.message.mentions[0]
        except IndexError:
            embed = self.bot.embed_template(title='Mention a user in the command to remove them')
            await ctx.send(embed=embed)
        else:
            removed = await self.bot.db_helper.delete_queued_users(ctx.guild.id, removee.id)
            name = removee.nick if removee.nick is not None else removee.display_name

            if removee.id in removed:
                title = f'**{name}** has been removed from the queue'
            else:
                title = f'**{name}** is not in the queue'

            embed = await self.queue_embed(ctx.guild, title)

            # Update queue display message
            await self.update_last_msg(ctx, embed)

    @commands.command(brief='Empty the queue (must have server kick perms)')
    @commands.has_permissions(kick_members=True)
    async def empty(self, ctx):
        """ Reset the guild queue list to empty. """
        await self.bot.db_helper.delete_all_queued_users(ctx.guild.id)
        embed = await self.queue_embed(ctx.guild, 'The queue has been emptied')

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
                      brief='Set or view the capacity of the queue (must have admin perms)')
    @commands.has_permissions(administrator=True)
    async def cap(self, ctx, *args):
        """ Set the queue capacity. """
        guild_data = await self.bot.db_helper.get_guild(ctx.guild.id)
        capacity = guild_data['capacity']
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
                    await self.bot.db_helper.delete_all_queued_users(ctx.guild.id)
                    await self.bot.db_helper.update_guild(ctx.guild.id, capacity=new_cap)
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
                      brief='Ban all mentioned users from joining the queue (must have server ban perms)')
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

        # Get user IDs to ban from mentions and insert them into ban table
        user_ids = [user.id for user in ctx.message.mentions]
        await self.bot.db_helper.insert_banned_users(ctx.guild.id, *user_ids, unban_time=unban_time)

        # Remove banned users from the queue
        for user in ctx.message.mentions:
            await self.bot.db_helper.delete_queued_users(ctx.guild.id, *user_ids)

        # Generate embed and send message
        banned_users_str = ', '.join(f'**{user.display_name}**' for user in ctx.message.mentions)
        ban_time_str = '' if unban_time is None else f' for {self.timedelta_str(time_delta)}'
        embed = self.bot.embed_template(title=f'Banned {banned_users_str}{ban_time_str}')
        embed.set_footer(text='Banned users have been removed from the queue')
        await ctx.send(embed=embed)

    @commands.command(usage='unban <user mention> ...',
                      brief='Unban all mentioned users so they can join the queue (must have server ban perms)')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx):
        """ Unban users mentioned in the command so they can join the queue. """
        # Check that users are mentioned
        if len(ctx.message.mentions) == 0:
            embed = self.bot.embed_template(title='Mention a user in the command to unban them')
            await ctx.send(embed=embed)
            return

        # Get user IDs to unban from mentions and delete them from the ban table
        user_ids = [user.id for user in ctx.message.mentions]
        unbanned_ids = await self.bot.db_helper.delete_banned_users(ctx.guild.id, *user_ids)

        # Generate embed and send message
        unbanned_users = [user for user in ctx.message.mentions if user.id in unbanned_ids]
        never_banned_users = [user for user in ctx.message.mentions if user.id not in unbanned_ids]
        unbanned_users_str = ', '.join(f'**{user.display_name}**' for user in unbanned_users)
        never_banned_users_str = ', '.join(f'**{user.display_name}**' for user in never_banned_users)
        title_1 = 'nobody' if unbanned_users_str == '' else unbanned_users_str
        were_or_was = 'were' if len(never_banned_users) > 1 else 'was'
        title_2 = '' if never_banned_users_str == '' else f' ({never_banned_users_str} {were_or_was} never banned)'
        embed = self.bot.embed_template(title=f'Unbanned {title_1}{title_2}')
        embed.set_footer(text='Unbanned users may now join the queue')
        await ctx.send(embed=embed)
