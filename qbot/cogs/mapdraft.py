#!/usr/bin/env python3
# mapdraft.py
# cameronshinn

import discord
from discord.ext import commands


class Map:
    """ A group of attributes representing a map. """

    def __init__(self, name, dev_name, emoji, image_url):
        """ Set attributes. """
        self.name = name
        self.dev_name = dev_name
        self.emoji = emoji
        self.image_url = image_url


de_cache = Map('Cache', 'de_cache', '<:de_cache:632416021910650919>',
            'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/maps/images/cache.jpg')
de_cbble = Map('Cobblestone', 'de_cbble', '<:de_cbble:632416085899214848>',
            'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/maps/images/cobblestone.jpg')
de_dust2 = Map('Dust II', 'de_dust2', '<:de_dust2:632416148658323476>',
            'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/maps/images/dust-ii.jpg')
de_inferno = Map('Inferno', 'de_inferno', '<:de_inferno:632416390112084008>',
              'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/maps/images/inferno.jpg')
de_mirage = Map('Mirage', 'de_mirage', '<:de_mirage:632416441551028225>',
             'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/maps/images/mirage.jpg')
de_nuke = Map('Nuke', 'de_nuke', '<:de_nuke:632416475029962763>',
           'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/maps/images/nuke.jpg')
de_overpass = Map('Overpass', 'de_overpass', '<:de_overpass:632416513562902529>',
               'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/maps/images/overpass.jpg')
de_train = Map('Train', 'de_train', '<:de_train:632416540687335444>',
            'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/maps/images/train.jpg')
de_vertigo = Map('Vertigo', 'de_vertigo', '<:de_vertigo:632416584870395904>',
              'https://raw.githubusercontent.com/cameronshinn/csgo-queue-bot/master/assets/maps/images/vertigo.jpg')

ALL_MAPS = [
    de_cache,
    de_cbble,
    de_dust2,
    de_inferno,
    de_mirage,
    de_nuke,
    de_overpass,
    de_train,
    de_vertigo
]

DEFAULT_MAP_POOL = [
    de_dust2,
    de_inferno,
    de_mirage,
    de_nuke,
    de_overpass,
    de_train,
    de_vertigo
]


class MDraftData:
    """ Holds guild-specific map draft data. """

    def __init__(self, map_pool=DEFAULT_MAP_POOL, maps_left=None, message=None):
        self.map_pool = map_pool
        self.maps_left = maps_left
        self.message = message


class MapDraftCog(commands.Cog):
    """ Handles the map drafter. """

    footer = 'React to any of the map icons below to ban the corresponding map'

    def __init__(self, bot, color):
        """ Set attributes. """
        self.bot = bot
        self.color = color
        self.guild_mdraft_data = {}  # Map guild -> guild map draft data

    @commands.Cog.listener()
    async def on_ready(self):
        """" Initialize mdraft data for each guild the bot is in. """
        for guild in self.bot.guilds:
            if guild not in self.guild_mdraft_data:  # Don't add if guild already loaded
                self.guild_mdraft_data[guild] = MDraftData()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """ Initialize an empty mdraft data object for guilds that are added. """
        self.guild_mdraft_data[guild] = MDraftData()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """ Remove mdraft data when a guild is removed. """
        self.guild_mdraft_data.pop(guild)

    async def cog_before_invoke(self, ctx):
        """ Trigger typing at the start of every command. """
        await ctx.trigger_typing()

    def maps_left_str(self, guild):
        """ Get the maps left string representation for a given giuld. """
        x_emoji = ':heavy_multiplication_x:'
        mdraft_data = self.guild_mdraft_data[guild]
        maps_left = mdraft_data.map_pool if mdraft_data.maps_left is None else mdraft_data.maps_left
        out_str = ''

        for m in mdraft_data.map_pool:
            out_str += f'{m.emoji}  {m.name}\n' if m in maps_left else f'{x_emoji}  ~~{m.name}~~\n'

        return out_str

    @commands.command(brief='Start (or restart) a map draft')
    async def mdraft(self, ctx):
        """ Start a map draft by sending a map draft embed panel. """
        mdraft_data = self.guild_mdraft_data[ctx.guild]
        mdraft_data.maps_left = mdraft_data.map_pool.copy()  # Set or reset map pool
        embed = discord.Embed(title='Map draft has begun!', description=self.maps_left_str(ctx.guild), color=self.color)
        embed.set_footer(text=MapDraftCog.footer)
        msg = await ctx.send(embed=embed)
        await msg.edit(embed=embed)

        for m in mdraft_data.map_pool:
            await msg.add_reaction(m.emoji)

        mdraft_data.message = msg

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """ Remove a map from the draft when a user reacts with the corresponding icon. """
        if user == self.bot.user:
            return

        guild = user.guild
        mdraft_data = self.guild_mdraft_data[guild]

        if mdraft_data.message is None or reaction.message.id != mdraft_data.message.id:
            return

        maps_left = mdraft_data.maps_left

        for m in mdraft_data.maps_left.copy():  # Iterate over copy to modify original w/o consequences
            if str(reaction.emoji) == m.emoji:
                async for u in reaction.users():
                    await reaction.remove(u)

                mdraft_data.maps_left.remove(m)

                if len(mdraft_data.maps_left) == 1:
                    map_result = mdraft_data.maps_left[0]
                    await mdraft_data.message.clear_reactions()
                    embed_title = f'We\'re going to {map_result.name}! {map_result.emoji}'
                    embed = discord.Embed(title=embed_title, color=self.color)
                    embed.set_image(url=map_result.image_url)
                    embed.set_footer(text=f'Be sure to select {map_result.name} in the PopFlash lobby')
                    await mdraft_data.message.edit(embed=embed)
                    mdraft_data.maps_left = None
                    mdraft_data.message = None
                else:
                    embed_title = f'**{user.name}** has banned **{m.name}**'
                    embed = discord.Embed(title=embed_title, description=self.maps_left_str(guild), color=self.color)
                    embed.set_thumbnail(url=m.image_url)
                    embed.set_footer(text=MapDraftCog.footer)
                    await mdraft_data.message.edit(embed=embed)

                break

    @commands.command(usage='q!setmp {+|-}<map name> ...',
                      brief='Add or remove maps from the mdraft map pool (Must have admin perms)')
    @commands.has_permissions(administrator=True)
    def setmp(self, ctx, *args):
        """"""
        if len(args) == 0:
            pass
        else:
            for arg in args:
                map_name = arg[1:]  # Remove +/- prefix
                map_obj = next((m for m in map_pool if m.dev_name == map_name), None)

                if arg.startswith('+'):
                    if map_obj is None:
                        pass
                    else:
                        pass
                elif arg.startswith('-'):
                    if map_obj is None:
                        pass
                    else:
                        pass
                else:
                    pass
