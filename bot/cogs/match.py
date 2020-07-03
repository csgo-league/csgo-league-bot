# match.py

import aiohttp
import asyncio
import discord
from discord.ext import commands
import random
import sys
import traceback


class PickError(ValueError):
    """ Raised when a team draft pick is invalid for some reason. """

    def __init__(self, message):
        """ Set message parameter. """
        self.message = message


class TeamDraftMenu(discord.Message):
    """ Message containing the components for a team draft. """

    def __init__(self, message, bot, users):
        """ Copy constructor from a message and specific team draft args. """
        # Copy all attributes from message object
        for attr_name in message.__slots__:
            try:
                attr_val = getattr(message, attr_name)
            except AttributeError:
                continue

            setattr(self, attr_name, attr_val)

        # Add custom attributes
        self.bot = bot
        self.users = users
        emoji_numbers = [u'\u0031\u20E3',
                         u'\u0032\u20E3',
                         u'\u0033\u20E3',
                         u'\u0034\u20E3',
                         u'\u0035\u20E3',
                         u'\u0036\u20E3',
                         u'\u0037\u20E3',
                         u'\u0038\u20E3',
                         u'\u0039\u20E3',
                         u'\U0001F51F']
        self.pick_emojis = dict(zip(emoji_numbers, users))
        self.pick_order = '12211221'
        self.pick_number = None
        self.users_left = None
        self.teams = None
        self.future = None

    @property
    def _active_picker(self):
        """ Get the active picker using the pick order and nummber. """
        if self.pick_number is None:
            return None

        picking_team_number = int(self.pick_order[self.pick_number])
        picking_team = self.teams[picking_team_number - 1]  # Subtract 1 to get team's index

        if len(picking_team) == 0:
            return None

        return picking_team[0]

    def _picker_embed(self, title):
        """ Generate the menu embed based on the current status of the team draft. """
        embed = self.bot.embed_template(title=title)
        embed.set_footer(text='React to any of the numbers below to pick the corresponding user')

        for team in self.teams:
            team_name = '__Team__' if len(team) == 0 else f'__Team {team[0].display_name}__'

            if len(team) == 0:
                team_players = '_Empty_'
            else:
                team_players = '\n'.join(p.display_name for p in team)

            embed.add_field(name=team_name, value=team_players)

        users_left_str = ''

        for emoji, user in self.pick_emojis.items():
            if not any(user in team for team in self.teams):
                users_left_str += f'{emoji}  {user.display_name}\n'
            else:
                users_left_str += f':heavy_multiplication_x:  ~~{user.display_name}~~\n'

        embed.insert_field_at(1, name='__Players Left__', value=users_left_str)
        return embed

    def _pick_player(self, picker, pickee):
        """ Process a team captain's player pick, assuming the picker is in the team draft. """
        # Get picking team
        if self.teams[0] == []:
            picking_team = self.teams[0]
            self.users_left.remove(picker)
            picking_team.append(picker)
        elif self.teams[1] == [] and picker != self.teams[0][0]:
            picking_team = self.teams[1]
            self.users_left.remove(picker)
            picking_team.append(picker)
        elif picker == self.teams[0][0]:
            picking_team = self.teams[0]
        elif picker == self.teams[1][0]:
            picking_team = self.teams[1]
        else:
            raise PickError(f'Picker {picker.display_name} is not a team captain')

        # Check if it's picker's turn
        if picker != self._active_picker:
            raise PickError(f'It is not {picker.display_name}\'s turn to pick')

        # Prevent picks when team is full
        if len(picking_team) > len(self.users) // 2:
            raise PickError(f'Team {picker.display_name} is full')

        # Add pickee to team if user didn't pick themselves (which is only possible picking first as a volunteer)
        if not picker == pickee:
            self.users_left.remove(pickee)
            picking_team.append(pickee)
            self.pick_number += 1

    async def _update_menu(self, title):
        """ Update the message to reflect the current status of the team draft. """
        await self.edit(embed=self._picker_embed(title))
        items = self.pick_emojis.items()
        awaitables = [self.clear_reaction(emoji) for emoji, user in items if user not in self.users_left]
        await asyncio.gather(*awaitables, loop=self.bot.loop)

    async def _process_pick(self, reaction, user):
        """ Handler function for player pick reactions. """
        # Check that reaction is on this message and user is in the team draft
        if reaction.message.id != self.id or user not in self.users:
            return

        # Check that picked player is in the player pool
        pick = self.pick_emojis.get(str(reaction.emoji), None)

        if pick is None or pick not in self.users_left:
            return

        # Attempt to pick the player for the team
        try:
            self._pick_player(user, pick)
        except PickError as e:  # Player not picked
            title = e.message
        else:  # Player picked
            title = f'**Team {user.display_name}** picked {pick.display_name}'

        if len(self.users_left) == 1:
            fat_kid_team = self.teams[0] if len(self.teams[0]) <= len(self.teams[1]) else self.teams[1]
            fat_kid_team.append(self.users_left.pop(0))

        if len(self.users_left) == 0:
            if self.future is not None:
                self.future.set_result(None)

            return

        await self._update_menu(title)

    async def draft(self):
        """ Start the team draft and return the teams after it's finished. """
        # Initialize draft
        guild_data = await self.bot.db_helper.get_guild(self.guild.id)
        self.users_left = self.users.copy()  # Copy users to edit players remaining in the player pool
        self.teams = [[], []]
        self.pick_number = 0
        captain_method = guild_data['captain_method']

        # Check captain methods
        if captain_method == 'rank':
            players = await self.bot.api_helper.get_players([user.id for user in self.users_left])
            players.sort(reverse=True, key=lambda x: x.score)

            for team in self.teams:
                captain = self.bot.get_user(players.pop(0).discord)
                self.users_left.remove(captain)
                team.append(captain)
        elif captain_method == 'random':
            temp_users = self.users_left.copy()
            random.shuffle(temp_users)

            for team in self.teams:
                captain = temp_users.pop()
                self.users_left.remove(captain)
                team.append(captain)
        elif captain_method == 'volunteer':
            pass
        else:
            raise ValueError(f'Captain method "{captain_method}" isn\'t valid')

        # Edit input message and add emoji button reactions
        await self.edit(embed=self._picker_embed('Team draft has begun!'))

        items = self.pick_emojis.items()
        for emoji, user in items:
            if user in self.users_left:
                await self.add_reaction(emoji)

        # Add listener handlers and wait until there are no users left to pick
        self.future = self.bot.loop.create_future()
        self.bot.add_listener(self._process_pick, name='on_reaction_add')
        await asyncio.wait_for(self.future, 600)
        self.bot.remove_listener(self._process_pick, name='on_reaction_add')
        await self.clear_reactions()

        # Return class to original state after team drafting is done
        picked_teams = self.teams
        self.pick_number = None
        self.users_left = None
        self.teams = None
        self.future = None

        return picked_teams


class MatchCog(commands.Cog):
    """ Handles everything needed to create matches. """

    def __init__(self, bot):
        """ Set attributes. """
        self.bot = bot
        self.pending_ready_tasks = {}

    async def draft_teams(self, message, users):
        """ Create a TeamDraftMenu from an existing message and run the draft. """
        menu = TeamDraftMenu(message, self.bot, users)
        teams = await menu.draft()
        return teams[0], teams[1]

    async def autobalance_teams(self, users):
        """ Balance teams based on players' RankMe score. """
        # Only balance teams with even amounts of players
        if len(users) % 2 != 0:
            raise ValueError('Users argument must have even length')

        # Get players and sort by RankMe score
        users_dict = dict(zip(await self.bot.api_helper.get_players([user.id for user in users]), users))
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

        return list(map(users_dict.get, team_one)), list(map(users_dict.get, team_two))

    @staticmethod
    async def randomize_teams(users):
        """ Randomly split a list of users in half. """
        temp_users = users.copy()
        random.shuffle(temp_users)
        team_size = len(temp_users) // 2
        return temp_users[:team_size], temp_users[team_size:]

    def teams_embed(self, title, team_one, team_two):
        """"""
        embed = self.bot.embed_template(title=title)
        embed.add_field(name='__Team 1__', value='\n'.join(user.mention for user in team_one))
        embed.add_field(name='__Team 2__', value='\n'.join(user.mention for user in team_two))
        return embed

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
            if ctx.guild in self.pending_ready_tasks:
                self.pending_ready_tasks[ctx.guild].close()

            self.pending_ready_tasks[ctx.guild.id] = self.bot.wait_for('reaction_add', timeout=60.0, check=all_ready)
            await self.pending_ready_tasks[ctx.guild]
        except asyncio.TimeoutError:  # Not everyone readied up
            unreadied = set(users) - reactors
            awaitables = [
                ready_message.clear_reactions(),
                self.bot.db_helper.delete_queued_users(ctx.guild.id, *(user.id for user in unreadied))
            ]
            await asyncio.gather(*awaitables, loop=self.bot.loop)
            description = '\n'.join(':heavy_multiplication_x:  ' + user.mention for user in unreadied)
            title = 'Not everyone was ready!'
            burst_embed = self.bot.embed_template(title=title, description=description)
            burst_embed.set_footer(text='The missing players have been removed from the queue')
            await ready_message.edit(embed=burst_embed)
            return False  # Not everyone readied up
        else:  # Everyone readied up
            self.pending_ready_tasks.pop(ctx.guild)
            # Attempt to make teams and start match
            awaitables = [
                ready_message.clear_reactions(),
                self.bot.db_helper.get_guild(ctx.guild.id)
            ]
            results = await asyncio.gather(*awaitables, loop=self.bot.loop)
            team_method = results[1]['team_method']

            if team_method == 'autobalance':
                team_one, team_two = await self.autobalance_teams(users)
            elif team_method == 'captains':
                team_one, team_two = await self.draft_teams(ready_message, users)
            elif team_method == 'random':
                team_one, team_two = await self.randomize_teams(users)
            else:
                raise ValueError(f'Team method "{team_method}" isn\'t valid')

            burst_embed = self.bot.embed_template(description='Fetching server...')
            await ready_message.edit(embed=burst_embed)

            # Check if able to get a match server and edit message embed accordingly
            try:
                match = await self.bot.api_helper.start_match(team_one, team_two)  # Request match from API
            except aiohttp.ClientResponseError as e:
                description = 'Sorry! Looks like there aren\'t any servers available at this time. ' \
                              'Please try again later.'
                burst_embed = self.bot.embed_template(title='There was a problem!', description=description)
                traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)  # Print exception to stderr
            else:
                description = f'URL: {match.connect_url}\nCommand: `{match.connect_command}`'
                burst_embed = self.bot.embed_template(title='Match server is ready!', description=description)

                for team in [team_one, team_two]:
                    team_name = f'__Team {team[0].display_name}__'
                    burst_embed.add_field(name=team_name, value='\n'.join(user.mention for user in team))

                burst_embed.set_footer(text='Server will close after 5 minutes if anyone doesn\'t join')

            await ready_message.edit(embed=burst_embed)
            return True  # Everyone readied up

    @commands.command(usage='teams [{captains|autobalance|random}]',
                      brief='Set or view the team creation method (must have admin perms)')
    @commands.has_permissions(administrator=True)
    async def teams(self, ctx, method=None):
        """ Set or display the method by which teams are created. """
        guild_data = await self.bot.db_helper.get_guild(ctx.guild.id)
        team_method = guild_data['team_method']
        valid_methods = ['captains', 'autobalance', 'random']

        if method is None:
            title = f'The current team creation method is {team_method}'
        else:
            method = method.lower()

            if method == team_method:
                title = f'The current team creation method is already set to {team_method}'
            elif method in valid_methods:
                title = f'Team creation method set to {method}'
                await self.bot.db_helper.update_guild(ctx.guild.id, team_method=method)
            else:
                title = f'Team creation method must be {valid_methods[0]}, {valid_methods[1]} or {valid_methods[2]}'

        embed = self.bot.embed_template(title=title)
        await ctx.send(embed=embed)

    @commands.command(usage='captains [{volunteer|rank|random}]',
                      brief='Set or view the captain selection method (must have admin perms)')
    @commands.has_permissions(administrator=True)
    async def captains(self, ctx, method=None):
        """ Set or display the method by which captains are selected. """
        guild_data = await self.bot.db_helper.get_guild(ctx.guild.id)
        captain_method = guild_data['captain_method']
        valid_methods = ['volunteer', 'rank', 'random']

        if method is None:
            title = f'The current captain selection method is {captain_method}'
        else:
            method = method.lower()

            if method == captain_method:
                title = f'The current captain selection method is already set to {captain_method}'
            elif method in valid_methods:
                title = f'Captain selection method set to {method}'
                await self.bot.db_helper.update_guild(ctx.guild.id, captain_method=method)
            else:
                title = f'Captain selection method must be {valid_methods[0]}, {valid_methods[1]} or {valid_methods[2]}'

        embed = self.bot.embed_template(title=title)
        await ctx.send(embed=embed)

    @teams.error
    @captains.error
    async def config_error(self, ctx, error):
        """ Respond to a permissions error with an explanation message. """
        if isinstance(error, commands.MissingPermissions):
            await ctx.trigger_typing()
            missing_perm = error.missing_perms[0].replace('_', ' ')
            title = f'Cannot set {ctx.command.name} method without {missing_perm} permission!'
            embed = self.bot.embed_template(title=title)
            await ctx.send(embed=embed)
