# context.py

from discord.ext import commands

from .map import MapPool
from .db import DBHelper


class LeagueBotContext(commands.Context):
    """"""
    # async with self.bot.db_pool.acquire() as connection:
    #     db = DBHelper(connection)
    #     db.get_queued_users(self.guild.id)
    #     db.get_banned_users(self.guild.id)
    #     db.get_guild(self.guild.id)

    async def queued_users(self):
        user_ids = await self.bot.db_helper.get_queued_users(self.guild.id)
        return self.bot.get_users(user_ids)

    async def queue_banlist(self):
        user_ids = await self.bot.db_helper.get_banned_users(self.guild.id)
        return self.bot.get_users(user_ids)

    async def guild_map_pool(self):
        guild_data = await self.bot.db_helper.get_guild(self.guild.id)
        return MapPool.from_dict(guild_data)
