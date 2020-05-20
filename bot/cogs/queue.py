# queue.py

import discord
from discord.ext import commands
import asyncio
import aiohttp
import random


class QueueCog(commands.Cog):
    """ Cog to manage queues of players among multiple servers. """

    def __init__(self, bot):
        """ Set attributes. """
        self.bot = bot
        self.guild_queues = {}  # Maps Guild: QQueue
        self.last_queue_msgs = {}

    async def queue_embed(self, guild, title=None):
        """ Method to create the queue embed for a guild. """
        queued_ids = await self.bot.db_helper.get_queued_users(guild)
        guild_data = await self.bot.db_helper.get_guild(guild)
        capacity = guild_data['capacity']

        if title:
            title += f' ({len(queued_ids)}/{capacity})'

        if len(queued_ids) == 0:  # If there are users in the queue
            queue_str = '_The queue is empty..._'
        else:  # No users in queue
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

    async def autobalance_teams(self, users):
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

    async def randomize_teams(self, users):
        """ Randomly split a list of users in half. """
        random.shuffle(users)
        team_size = len(users) // 2
        return users[:team_size], users[team_size:]

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
            await self.bot.db_helper.delete_queued_users(ctx.guild, *unreadied)
            description = '\n'.join(':heavy_multiplication_x:  ' + user.mention for user in unreadied)
            title = 'Not everyone was ready!'
            burst_embed = self.bot.embed_template(title=title, description=description)
            burst_embed.set_footer(text='The missing players have been removed from the queue')
            await ready_message.edit(embed=burst_embed)
            return False  # Not everyone readied up
        else:  # Everyone readied up
            # Attempt to make teams and start match
            await ready_message.clear_reactions()
            guild_data = await self.bot.db_helper.get_guild(ctx.guild)
            team_method = guild_data['team_method']

            if team_method == 'autobalance':
                team_one, team_two = await self.autobalance_teams(users)
            elif team_method == 'captains':
                teamdraft_cog = self.bot.get_cog('TeamDraftCog')
                team_one, team_two = await teamdraft_cog.draft_teams(ready_message, users)
            elif team_method == 'random':
                team_one, team_two = self.randomize_teams(users)
            else:
                raise ValueError(f'Team method "{team_method}" isn\'t valid')

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
        if not await self.bot.api.is_linked(ctx.author):  # Message author isn't linked
            title = f'Unable to add **{ctx.author.display_name}**: Their account is not linked'
        else:  # Message author is linked
            player = await self.bot.api.get_player(ctx.author)
            await self.bot.db_helper.insert_users(ctx.author)
            queue_ids = await self.bot.db_helper.get_queued_users(ctx.guild)
            queue = [self.bot.get_user(user_id) for user_id in queue_ids]
            guild_data = await self.bot.db_helper.get_guild(ctx.guild)
            capacity = guild_data['capacity']

            if ctx.author in queue:  # Author already in queue
                title = f'**{ctx.author.display_name}** is already in the queue'
            elif len(queue) >= capacity:  # Queue full
                title = f'Unable to add **{ctx.author.display_name}**: Queue is full'
            elif not player:  # ApiHelper couldn't get player
                title = f'Unable to add **{ctx.author.display_name}**: Cannot verify match status'
            elif player.in_match:  # User is already in a match
                title = f'Unable to add **{ctx.author.display_name}**: They are already in a match'
            else:  # User can be added
                await self.bot.db_helper.insert_queued_users(ctx.guild, ctx.author)
                queue += [ctx.author]
                title = f'**{ctx.author.display_name}** has been added to the queue'

                # Check and burst queue if full
                if len(queue) == capacity:
                    try:
                        all_readied = await self.start_match(ctx, queue)
                    except asyncio.TimeoutError:
                        return

                    if all_readied:
                        await self.bot.db_helper.delete_queued_users(ctx.guild, *queue)

                    return

        embed = await self.queue_embed(ctx.guild, title)

        # Delete last queue message
        await self.update_last_msg(ctx, embed)

    @commands.command(brief='Leave the queue (or the bursted queue)')
    async def leave(self, ctx):
        """ Check if the member can be remobed from the guild and remove them if so. """
        removed = await self.bot.db_helper.delete_queued_users(ctx.guild, ctx.author)

        if ctx.author.id in removed:
            title = f'**{ctx.author.display_name}** has been removed from the queue '
        else:
            title = f'**{ctx.author.display_name}** isn\'t in the queue '

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
            embed = discord.Embed(title='Mention a player in the command to remove them', color=self.bot.color)
            await ctx.send(embed=embed)
        else:
            removed = await self.bot.db_helper.delete_queued_users(ctx.guild, removee)

            if removee.id in removed:
                title = f'**{removee.display_name}** has been removed from the queue'
            else:
                title = f'**{removee.display_name}** is not in the queue'

            embed = await self.queue_embed(ctx.guild, title)

            # Update queue display message
            await self.update_last_msg(ctx, embed)

    @commands.command(brief='Empty the queue (must have server kick perms)')
    @commands.has_permissions(kick_members=True)
    async def empty(self, ctx):
        """ Reset the guild queue list to empty. """
        await self.bot.db_helper.delete_all_queued_users(ctx.guild)
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
            title = f'Cannot remove players without {missing_perm} permission!'
            embed = discord.Embed(title=title, color=self.bot.color)
            await ctx.send(embed=embed)

    @commands.command(brief='Set the capacity of the queue (Must have admin perms)')
    @commands.has_permissions(administrator=True)
    async def cap(self, ctx, *args):
        """ Set the queue capacity. """
        guild_data = await self.bot.db_helper.get_guild(ctx.guild)
        capacity = guild_data['capacity']

        if len(args) == 0:  # No size argument specified
            embed = discord.Embed(title=f'The current queue capacity is {capacity}', color=self.bot.color)
        else:
            new_cap = args[0]

            try:
                new_cap = int(new_cap)
            except ValueError:
                embed = discord.Embed(title=f'{new_cap} is not an integer', color=self.bot.color)
            else:
                if new_cap == capacity:
                    embed = discord.Embed(title=f'Capacity is already set to {capacity}', color=self.bot.color)
                elif new_cap < 2 or new_cap > 100:
                    embed = discord.Embed(title='Capacity is outside of valid range', color=self.bot.color)
                else:
                    await self.bot.db_helper.delete_all_queued_users(ctx.guild)
                    await self.bot.db_helper.update_guild(ctx.guild, capacity=new_cap)
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
