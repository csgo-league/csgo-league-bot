# context.py

import discord
from discord.ext import commands
from typing import List

from .config import GuildConfig
from .db import DBHelper
from .map import MapPool


class LeagueContext(commands.Context):
    """
    Custom context for the bot to implement streamlined database access.
    """

    async def queued_users(self):
        async with self.bot.db_pool.acquire() as conn:
            user_ids = await DBHelper(conn).get_queued_users(self.guild.id)

        return self.bot.get_users(user_ids)

    async def enqueue_users(self, *users):
        user_ids = (user.id for user in users)

        async with self.bot.db_pool.acquire() as conn:
            db_helper = DBHelper(conn)
            await db_helper.insert_users(*user_ids)
            await db_helper.insert_queued_users(self.guild.id, *user_ids)

    async def dequeue_users(self, *users):
        async with self.bot.db_pool.acquire() as conn:
            dequeued_ids = await DBHelper(conn).delete_queued_users(self.guild.id, *(user.id for user in users))

        return self.bot.get_users(dequeued_ids)

    async def empty_queue(self):
        async with self.bot.db_pool.acquire() as conn:
            cleared_ids = await DBHelper(conn).clear_queued_users(self.guild.id)

        return self.bot.get_users(cleared_ids)

    async def queue_banlist(self):
        async with self.bot.db_pool.acquire() as conn:
            banned_dict = await DBHelper(conn).get_banned_users(self.guild.id)

        return {self.bot.get_user(user_id): time for user_id, time in banned_dict.items()}

    async def ban_from_queue(self, *users, unban_time=None):
        user_ids = (user.id for user in users)

        async with self.bot.db_pool.acquire() as conn:
            db_helper = DBHelper(conn)
            await db_helper.insert_users(*user_ids)
            await db_helper.insert_banned_users(self.guild.id, *user_ids, unban_time=unban_time)

    async def unban_from_queue(self, *users) -> List[discord.User]:
        async with self.bot.db_pool.acquire() as conn:
            unbanned_ids = await DBHelper(conn).delete_banned_users(self.guild.id, *(user.id for user in users))

        return self.bot.get_users(unbanned_ids)

    async def guild_config(self) -> GuildConfig:
        async with self.bot.db_pool.acquire() as conn:
            guild_data = await DBHelper(conn).get_guild(self.guild.id)

        return GuildConfig.from_dict(guild_data)

    async def set_guild_config(self, *, guild_config: GuildConfig = None, map_pool: MapPool = None, **kwargs) -> None:
        if guild_config is not None:
            guild_data = guild_config.to_dict
        elif map_pool is not None:
            guild_data = map_pool.to_dict
        else:
            guild_data = kwargs

        async with self.bot.db_pool.acquire() as conn:
            await DBHelper(conn).update_guild(self.guild.id, **guild_data)
