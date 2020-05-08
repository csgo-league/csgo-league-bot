# queue.py

import discord
from discord.ext import commands
import asyncio
import aiohttp

BALANCE_TEAMS = False  # TODO: Implement a way to decide if teams should be balanced


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
        self.guild_queues = {}  # Maps Guild: QQueue

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

        embed = self.bot.embed_template(title=title, description=queue_str)
        embed.set_footer(text='Players will receive a notification when the queue fills up')
        return embed

    async def balance_teams(self, users):
        """ Balance teams based on players' RankMe score. """
        # Only balance teams with even amounts of players
        if len(users) % 2 != 0:
            raise ValueError('Argument "users" must have even length')

        # Get players and sort by RankMe score
        users_dict = dict(zip(await self.bot.api.get_players(users), users))
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
        burst_embed = self.bot.embed_template(title='Queue has filled up!', description=description)
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
                try:
                    users.remove(user)  # Modifies users in the scope where this function is called
                except ValueError:
                    pass

            description = '\n'.join(':heavy_multiplication_x:  ' + user.mention for user in unreadied)
            title = 'Not everyone was ready!'
            burst_embed = self.bot.embed_template(title=title, description=description)
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
                team_one, team_two = await teamdraft_cog.draft_teams(ready_message, users)

            await asyncio.sleep(5)  # Wait for users to see the final teams
            title = ''
            burst_embed = self.bot.embed_template(title=title, description='Fetching server...')
            await ready_message.edit(embed=burst_embed)

            # Check if able to get a match server and edit message embed accordingly
            try:
                match = await self.bot.api.start_match(team_one, team_two)  # Request match from API
            except aiohttp.ClientResponseError:
                description = 'Sorry! Looks like there aren\'t any servers available at this time. ' \
                              'Please try again later.'
                burst_embed = self.bot.embed_template(title='There was a problem!', description=description)
            else:
                description = f'URL: {match.connect_url}\nCommand: `{match.connect_command}`'
                burst_embed = self.bot.embed_template(title='Server ready!', description=description)
                burst_embed.set_footer(text='Server will close after 5 minutes if anyone doesn\'t join')

            await ready_message.edit(embed=burst_embed)
            return True  # Everyone readied up

    @commands.command(brief='Join the queue')
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)  # Only process one command per guild at once
    async def join(self, ctx):
        """ Check if the member can be added to the guild queue and add them if so. """
        queue = self.guild_queues[ctx.guild]

        if not await self.bot.api.is_linked(ctx.author):  # Message author isn't linked
            title = f'Unable to add **{ctx.author.display_name}**: Their account is not linked'
        else:  # Message author is linked
            player = await self.bot.api.get_player(ctx.author)

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
                    try:
                        all_readied = await self.start_match(ctx, queue.active)
                    except asyncio.TimeoutError:
                        return

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
