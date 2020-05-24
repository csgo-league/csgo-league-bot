# match.py

import aiohttp
import asyncio
import discord
from discord.ext import commands
import random


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
        self.users_left = None
        self.teams = None
        self.future = None

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
        """ Process a team captain's player pick. """
        if any(team == [] for team in self.teams) and picker in self.users:
            picking_team = self.teams[self.teams.index([])]  # Get the first empty team
            self.users_left.remove(picker)
            picking_team.append(picker)
        elif picker == self.teams[0][0]:
            picking_team = self.teams[0]
        elif picker == self.teams[1][0]:
            picking_team = self.teams[1]
        elif picker in self.users:
            raise PickError(f'Picker {picker.mention} is not a team captain')
        else:
            raise PickError(f'Picker {picker.mention} is not a user in the team draft')

        if len(picking_team) > len(self.users) // 2:  # Team is full
            raise PickError(f'Team {picker.mention} is full')

        if not picker == pickee:
            self.users_left.remove(pickee)
            picking_team.append(pickee)

    async def _update_menu(self, title):
        """ Update the message to reflect the current status of the team draft. """
        await self.edit(embed=self._picker_embed(title))
        items = self.pick_emojis.items()
        awaitables = [self.clear_reaction(emoji) for emoji, user in items if user not in self.users_left]
        asyncio.gather(*awaitables, loop=self.bot.loop)

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
            title = 'Teams are set!'

            if self.future is not None:
                self.future.set_result(None)

        await self._update_menu(title)

    async def draft(self):
        """ Start the team draft and return the teams after it's finished. """
        # Initialize draft
        guild_data = await self.bot.db_helper.get_guild(self.guild.id)
        self.users_left = self.users.copy()  # Copy users to edit players remaining in the player pool
        self.teams = [[], []]
        captain_method = guild_data['captain_method']

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

        await self.edit(embed=self._picker_embed('Team draft has begun!'))

        for emoji in self.pick_emojis:
            await self.add_reaction(emoji)

        # Add listener handlers and wait until there are no users left to pick
        self.future = self.bot.loop.create_future()
        self.bot.add_listener(self._process_pick, name='on_reaction_add')
        await asyncio.wait_for(self.future, 600)
        self.bot.remove_listener(self._process_pick, name='on_reaction_add')

        return self.teams


class MatchCog(commands.Cog):
    """ Handles everything needed to create matches. """

    def __init__(self, bot):
        """ Set attributes. """
        self.bot = bot

    async def draft_teams(self, message, users):
        """ Create a TeamDraftMenu from an existing message and run the draft. """
        menu = TeamDraftMenu(message, self.bot, users)
        teams = await menu.draft()
        return teams[0], teams[1]

    async def autobalance_teams(self, user_ids):
        """ Balance teams based on players' RankMe score. """
        # Only balance teams with even amounts of players
        if len(user_ids) % 2 != 0:
            raise ValueError('Users argument must have even length')

        # Get players and sort by RankMe score
        users_dict = dict(zip(await self.bot.api_helper.get_players(user_ids), user_ids))
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

    @staticmethod
    async def randomize_teams(users):
        """ Randomly split a list of users in half. """
        temp_users = users.copy()
        random.shuffle(temp_users)
        team_size = len(temp_users) // 2
        return temp_users[:team_size], temp_users[team_size:]

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
            unreadied = set(users) - reactors
            awaitables = [
                ready_message.clear_reactions(),
                self.bot.db_helper.delete_queued_users(ctx.guild.id, *(user.id for user in unreadied))
            ]
            asyncio.gather(*awaitables, loop=self.bot.loop)
            description = '\n'.join(':heavy_multiplication_x:  ' + user.mention for user in unreadied)
            title = 'Not everyone was ready!'
            burst_embed = self.bot.embed_template(title=title, description=description)
            burst_embed.set_footer(text='The missing players have been removed from the queue')
            await ready_message.edit(embed=burst_embed)
            return False  # Not everyone readied up
        else:  # Everyone readied up
            # Attempt to make teams and start match
            await ready_message.clear_reactions()
            guild_data = await self.bot.db_helper.get_guild(ctx.guild.id)
            team_method = guild_data['team_method']

            if team_method == 'autobalance':
                team_one, team_two = await self.autobalance_teams([user.id for user in users])
                await asyncio.sleep(8)
            elif team_method == 'captains':
                team_one, team_two = await self.draft_teams(ready_message, users)
                await asyncio.sleep(3)
            elif team_method == 'random':
                team_one, team_two = self.randomize_teams(users)
                await asyncio.sleep(8)
            else:
                raise ValueError(f'Team method "{team_method}" isn\'t valid')

            title = ''
            burst_embed = self.bot.embed_template(title=title, description='Fetching server...')
            await ready_message.edit(embed=burst_embed)

            # Check if able to get a match server and edit message embed accordingly
            try:
                match = await self.bot.api_helper.start_match(team_one, team_two)  # Request match from API
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
