# queue.py

import discord
from discord.ext import commands
import asyncio

BALANCE_TEAMS = False


class QQueue:
    """ Queue class for the bot. """

    def __init__(self, active=None, capacity=10, bursted=None, timeout=None, last_msg=None):
        """ Set attributes. """
        # Assign empty lists inside function to make them unique to objects
        self.active = [] if active is None else active  # List of players in the queue
        self.capacity = capacity  # Max queue size
        self.bursted = [] if bursted is None else bursted  # Cached last filled queue
        self.last_msg = last_msg  # Last sent confirmation message for the join command

    @property
    def is_default(self):
        """ Indicate whether the QQueue has any non-default values. """
        return self.active == [] and self.capacity == 10 and self.bursted == []


class QueueCog(commands.Cog):
    """ Cog to manage queues of players among multiple servers. """

    def __init__(self, bot):
        """ Set attributes. """
        self.bot = bot
        self.guild_queues = {}  # Maps Guild -> QQueue

    @commands.Cog.listener()
    async def on_ready(self):
        """ Initialize an empty list for each guild the bot is in. """
        for guild in self.bot.guilds:
            if guild not in self.guild_queues:  # Don't add empty queue if guild already loaded
                self.guild_queues[guild] = QQueue()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """ Initialize an empty list for guilds that are added. """
        self.guild_queues[guild] = QQueue()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """ Remove queue list when a guild is removed. """
        self.guild_queues.pop(guild)

    def queue_embed(self, guild, title=None):
        """ Method to create the queue embed for a guild. """
        queue = self.guild_queues[guild]

        if title:
            title += f' ({len(queue.active)}/{queue.capacity})'

        if queue.active != []:  # If there are users in the queue
            queue_str = ''.join(f'{e_usr[0]}. {e_usr[1].mention}\n' for e_usr in enumerate(queue.active, start=1))
        else:  # No users in queue
            queue_str = '_The queue is empty..._'

        embed = discord.Embed(title=title, description=queue_str, color=self.bot.color)
        embed.set_footer(text='Players will receive a notification when the queue fills up')
        return embed

    async def balance_teams(self, users):
        """ Balance teams based on players' RankMe score. """
        # Only balance teams with even amounts of players
        if len(users) % 2 != 0:
            return

        # Get players and sort by RankMe score
        users_dict = dict(zip(await self.bot.api_helper.get_players(users), users))
        players = list(users_dict.keys())
        players.sort(key=lambda x: x.score)

        # Balance teams
        team_size = len(players) // 2
        team_one = [players.pop()]
        team_two = [players.pop()]

        while players:
            if len(team_one) >= team_size:
                team_two.append(players.pop())
            elif len(team_two) >= team_size:
                team_one.append(players.pop())
            elif sum(p.score for p in team_one) < sum(p.score for p in team_two):
                team_one.append(players.pop())
            else:
                team_two.append(players.pop())

        return map(users_dict.get, team_one), map(users_dict.get, team_two)

    async def start_match(self, ctx, users):
        """ Ready all the users up and start a match. """
        # Notify everyone to ready up
        user_mentions = ''.join(user.mention for user in users)
        ready_emoji = '✅'
        description = f'React with the {ready_emoji} below to ready up (1 min)'
        burst_embed = discord.Embed(title='Queue has filled up!', description=description, color=self.bot.color)
        ready_message = await ctx.send(user_mentions, embed=burst_embed)
        await ready_message.add_reaction(ready_emoji)

        # Wait for everyone to ready up
        reactors = set()  # Track who has readied up

        def all_ready(reaction, user):
            """ Check if all players in the queue have readied up. """
            # Check if this is a reaction we care about
            if reaction.message.id != ready_message.id or user not in users or reaction.emoji != ready_emoji:
                return False

            reactors.add(user)

            if reactors.issuperset(users):  # All queued users have reacted
                return True
            else:
                return False

        try:
            await self.bot.wait_for('reaction_add', timeout=60.0, check=all_ready)
        except asyncio.TimeoutError:  # Not everyone readied up
            await ready_message.clear_reactions()
            unreadied = set(users) - reactors

            for user in unreadied:
                users.remove(user)  # Modifies users in the scope where this function is called

            description = '\n'.join('× ' + user.mention for user in unreadied)
            title = 'Not everyone was ready!'
            burst_embed = discord.Embed(title=title, description=description, color=self.bot.color)
            burst_embed.set_footer(text='The missing players have been removed from the queue')
            await ready_message.edit(embed=burst_embed)
            return False  # Not everyone readied up
        else:  # Everyone readied up
            # Attempt to make teams and start match
            await ready_message.clear_reactions()

            if BALANCE_TEAMS:
                team_one, team_two = await self.balance_teams(users)  # Get teams
            else:
                teamdraft_cog = self.bot.get_cog('TeamDraftCog')
                team_one, team_two = await teamdraft_cog.draft_teams(ctx, ready_message, users)

            await asyncio.sleep(5)  # Wait for users to see the final teams
            title = ''
            burst_embed = discord.Embed(title=title, description='Fetching server...', color=self.bot.color)
            await ready_message.edit(embed=burst_embed)

            match = await self.bot.api_helper.start_match(team_one, team_two)  # Request match from API

            # Check if able to get a match server and edit message embed accordingly
            if match:
                description = f'URL: {match.connect_url}\nCommand: `{match.connect_command}`'
                burst_embed = discord.Embed(title='Server ready!', description=description, color=self.bot.color)
                burst_embed.set_footer(text='Server will close after 5 minutes if anyone doesn\'t join')
            else:
                description = ('Sorry! Looks like there aren\'t any servers available at this time. ',
                               'Please try again later.')
                burst_embed = discord.Embed(title='There was a problem!', description=description, color=self.bot.color)

            await ready_message.edit(embed=burst_embed)
            return True  # Everyone readied up

    @commands.command(brief='Join the queue')
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)  # Only process one command per guild at once
    async def join(self, ctx):
        """ Check if the member can be added to the guild queue and add them if so. """
        queue = self.guild_queues[ctx.guild]

        if not await self.bot.api_helper.is_linked(ctx.author):  # Message author isn't linked
            title = f'Unable to add **{ctx.author.display_name}**: Their account is not linked'
        else:  # Message author is linked
            player = await self.bot.api_helper.get_player(ctx.author)

            if ctx.author in queue.active:  # Author already in queue
                title = f'**{ctx.author.display_name}** is already in the queue'
            elif len(queue.active) >= queue.capacity:  # Queue full
                title = f'Unable to add **{ctx.author.display_name}**: Queue is full'
            elif not player:  # ApiHelper couldn't get player
                title = f'Unable to add **{ctx.author.display_name}**: Cannot verify match status'
            elif player.in_match:  # User is already in a match
                title = f'Unable to add **{ctx.author.display_name}**: They are already in a match'
            else:  # User can be added
                queue.active.append(ctx.author)
                title = f'**{ctx.author.display_name}** has been added to the queue'

                # Check and burst queue if full
                if len(queue.active) == queue.capacity:
                    all_readied = await self.start_match(ctx, queue.active)

                    if all_readied:
                        queue.bursted = queue.active  # Save bursted queue for player draft
                        queue.active = []  # Reset the player queue to empty

                    return

        # Send message based on outcome
        embed = self.queue_embed(ctx.guild, title)

        # Delete last queue message
        if queue.last_msg:
            try:
                await queue.last_msg.delete()
            except discord.errors.NotFound:
                pass

        queue.last_msg = await ctx.send(embed=embed)

    @commands.command(brief='Leave the queue (or the bursted queue)')
    async def leave(self, ctx):
        """ Check if the member can be remobed from the guild and remove them if so. """
        queue = self.guild_queues[ctx.guild]

        if ctx.author in queue.active:
            queue.active.remove(ctx.author)
            title = f'**{ctx.author.display_name}** has been removed from the queue '
        else:
            title = f'**{ctx.author.display_name}** isn\'t in the queue '

        embed = self.queue_embed(ctx.guild, title)

        if queue.last_msg:
            try:
                await queue.last_msg.delete()
            except discord.errors.NotFound:
                pass

        queue.last_msg = await ctx.channel.send(embed=embed)

    @commands.command(brief='Display who is currently in the queue')
    async def view(self, ctx):
        """  Display the queue as an embed list of mentioned names. """
        queue = self.guild_queues[ctx.guild]
        embed = self.queue_embed(ctx.guild, 'Players in queue for 10-mans')

        if queue.last_msg:
            try:
                await queue.last_msg.delete()
            except discord.errors.NotFound:
                pass

        queue.last_msg = await ctx.send(embed=embed)

    @commands.command(usage='remove <user mention>',
                      brief='Remove the mentioned user from the queue (must have server kick perms)')
    @commands.has_permissions(kick_members=True)
    async def remove(self, ctx):
        """ Remove the specified user from the queue. """
        try:
            removee = ctx.message.mentions[0]
        except IndexError:
            embed = discord.Embed(title='Mention a player in the command to remove them', color=self.bot.color)
            await ctx.send(embed=embed)
        else:
            queue = self.guild_queues[ctx.guild]

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
                    burst_embed, user_mentions = self.burst_queue(ctx.guild)
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

            embed = self.queue_embed(ctx.guild, title)

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
        queue = self.guild_queues[ctx.guild]
        queue.active.clear()
        embed = self.queue_embed(ctx.guild, 'The queue has been emptied')

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
            embed = discord.Embed(title=title, color=self.bot.color)
            await ctx.send(embed=embed)

    @commands.command(brief='Set the capacity of the queue (Must have admin perms)')
    @commands.has_permissions(administrator=True)
    async def cap(self, ctx, *args):
        """ Set the queue capacity. """
        queue = self.guild_queues[ctx.guild]

        if len(args) == 0:  # No size argument specified
            embed = discord.Embed(title=f'The current queue capacity is {queue.capacity}', color=self.bot.color)
        else:
            new_cap = args[0]

            try:
                new_cap = int(new_cap)
            except ValueError:
                embed = discord.Embed(title=f'{new_cap} is not an integer', color=self.bot.color)
            else:
                if new_cap < 2 or new_cap > 100:
                    embed = discord.Embed(title='Capacity is outside of valid range', color=self.bot.color)
                else:
                    queue.active.clear()  # Empty active queue to prevent bugs related to capacity size
                    queue.capacity = new_cap
                    embed = discord.Embed(title=f'Queue capacity set to {new_cap}', color=self.bot.color)
                    embed.set_footer(text='The queue has been emptied because of the capacity change')

        await ctx.send(embed=embed)

    @cap.error
    async def cap_error(self, ctx, error):
        """ Respond to a permissions error with an explanation message. """
        if isinstance(error, commands.MissingPermissions):
            await ctx.trigger_typing()
            missing_perm = error.missing_perms[0].replace('_', ' ')
            title = f'Cannot change queue capacity without {missing_perm} permission!'
            embed = discord.Embed(title=title, color=self.bot.color)
            await ctx.send(embed=embed)
