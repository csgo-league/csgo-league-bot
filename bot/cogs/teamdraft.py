# teamdraft.py

import discord
from discord.ext import commands
import asyncio

EMOJI_NUMBERS = [u'\u0031\u20E3',
                 u'\u0032\u20E3',
                 u'\u0033\u20E3',
                 u'\u0034\u20E3',
                 u'\u0035\u20E3',
                 u'\u0036\u20E3',
                 u'\u0037\u20E3',
                 u'\u0038\u20E3',
                 u'\u0039\u20E3',
                 u'\U0001F51F']


class TeamDraftCog(commands.Cog):
    """ Handles the player drafter command. """

    def __init__(self, bot):
        """ Set attributes and initialize empty draft teams. """
        self.bot = bot
        self.guild_player_pool = {}  # Players participating in the draft for each guild
        self.guild_teams = {}  # Teams for each guild
        self.guild_msgs = {}  # Last team draft embed message sent for each guild

    @commands.Cog.listener()
    async def on_ready(self):
        """ Initialize an empty list for each giuld the bot is in. """
        for guild in self.bot.guilds:
            self.guild_player_pool[guild] = []
            self.guild_teams[guild] = [[], []]

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """ Initialize an empty list for guilds that are added. """
        self.guild_player_pool[guild] = []
        self.guild_teams[guild] = [[], []]

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """ Remove queue list when a guild is removed. """
        self.guild_player_pool.pop(guild, None)
        self.guild_teams.pop(guild, None)
        self.guild_msgs.pop(guild, None)

    async def cog_before_invoke(self, ctx):
        """ Trigger typing at the start of every command. """
        await ctx.trigger_typing()

    def team_draft_embed(self, title, all_users, team_1, team_2):
        """ Return the player draft embed based on the title, users and teams. """
        embed = discord.Embed(title=title, color=self.bot.color)
        embed.set_footer(text='React to any of the numbers below to pick the corresponding user')
        x_emoji = ':heavy_multiplication_x:'
        players_left_str = ''

        for num, user in zip(EMOJI_NUMBERS, all_users):
            if user not in team_1 and user not in team_2:
                players_left_str += f'{num}  {user.display_name}\n'
            else:
                players_left_str += f'{x_emoji}  ~~{user.display_name}~~\n'

        def embed_team(team):
            team_name = 'Team' if len(team) == 0 else f'Team {team[0].display_name}'

            if len(team) == 0:
                team_players = '_Empty_'
            else:
                team_players = '\n'.join(p.display_name for p in team)

            embed.add_field(name=f'__{team_name}__', value=team_players)

        embed_team(team_1)
        embed.add_field(name='__Players Left__', value=players_left_str, inline=True)
        embed_team(team_2)
        return embed

    async def draft_teams(self, ctx, message, users):
        """ Split the users into two teams from user input """
        users_left_dict = dict(zip(EMOJI_NUMBERS, users))  # Dict mapping the emojis to users
        teams = [[], []]
        embed = self.team_draft_embed('Team draft has begun!', users, *teams)  # FIXME?
        await message.edit(embed=embed)
        team_size = len(users) // 2

        for emoji in EMOJI_NUMBERS:
            await message.add_reaction(emoji)

        async def player_pick(reaction, reactor):
            """"""  # TODO
            # Check that the reaction is for the team draft
            if reaction.message.id != ctx.message.id or str(reaction.emoji) not in users_left_dict.keys():
                return False

            # Check if the person picking is valid and they didn't pick themselves
            if reactor == teams[0][0]:  # Picker is team 0 captain
                picking_team = teams[0]
            elif reactor == teams[1][0]:  # Picker is team 1 captain
                picking_team = teams[1]
            elif reactor in users:  # Picker is in the player pool
                if teams[0] == []:  # Team 1 empty
                    picking_team = teams[0]
                if teams[1] == []:  # Team 2 empty
                    picking_team = teams[1]
                else:  # New team cannot be created
                    return False

                picker_emoji = next([key for key, val in users_left_dict.items() if val == reactor])  # Get picker emoji
                await message.clear_reaction(picker_emoji)
                picking_team.append(users_left_dict.pop(picker_emoji))
            else:  # Picker isn't alowed to pick players
                return False

            if len(picking_team) >= team_size:  # Should never be greater than
                return False

            # Pick the player for the team
            await reaction.clear()
            player_pick = users_left_dict.pop(str(reaction.emoji))
            picking_team.append(player_pick)

            # Check if teams are picked
            if len(users_left_dict) == 1:
                await message.clear_reactions()
                smaller_team = min(teams, key=len)
                smaller_team.append(next(users_left_dict.values()))
                embed = self.team_draft_embed(f'Teams are set!', users, *teams)  # FIXME?
                await message.edit(embed=embed)
                return True
            else:
                title = f'**Team {reactor.display_name}** picked **{player_pick.display_name}**'
                embed = self.team_draft_embed(title, users, *teams)  # FIXME?
                await message.edit(embed=embed)
                return False

        try:
            self.bot.wait_for('reaction_add', timeout=600.0, check=player_pick)  # 10 minute timeout
        except asyncio.TimeoutError:
            return

        return teams[0], teams[1]

    # @commands.command(brief='Start (or restart) a player draft from the last popped queue')  # Omit command for now
    # async def tdraft(self, ctx):
    #     """ Start a player draft by sending a player draft embed panel. """
    #     queue_cog = self.bot.get_cog('QueueCog')

    #     if not queue_cog:
    #         return

    #     queue = queue_cog.guild_queues.get(ctx.guild)

    #     if len(queue.active) < queue.capacity:
    #         embed_title = f'Cannot start player draft until the queue is full ({len(queue.active)}/{queue.capacity})'
    #         embed = discord.Embed(title=embed_title, color=self.bot.color)
    #         await ctx.send(embed=embed)
    #         return

    #     teams = await self.draft_teams(ctx, queue.active)

    #     if not teams:
    #         return

    #     # FINISH HERE
