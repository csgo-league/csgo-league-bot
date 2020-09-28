# context.py

from discord.ext import commands

from .map import MapPool


class LeagueBotContext(commands.Context):
    """"""

    async def queued_users(self):
        user_ids = await self.bot.db_helper.get_queued_users(self.guild.id)
        return self.bot.get_users(user_ids)

    async def queue_banlist(self):
        user_ids = await self.bot.db_helper.get_banned_users(self.guild.id)
        return self.bot.get_users(user_ids)

    async def guild_map_pool(self):
        guild_data = await self.bot.db_helper.get_guild(self.guild.id)
        return MapPool.from_dict(guild_data)
