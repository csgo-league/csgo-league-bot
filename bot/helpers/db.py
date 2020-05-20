# db.py


class DBHelper:
    """ Class to contain database query wrapper functions. """

    def __init__(self, pool):
        """ Set attributes. """
        self.pool = pool

    @staticmethod
    def _get_record_attrs(records, key='id'):
        """ Get key list of attributes from list of Record objects. """
        return list(map(lambda r: r[key], records))

    async def _get_row(self, table, obj):
        """ Generic method to get table row by object id. """
        statement = (
            f'SELECT * FROM {table}\n'
            '   WHERE id = $1'
        )

        async with self.pool.acquire() as connection:
            async with connection.transaction():
                row = await connection.fetchrow(statement, obj.id)

        return {col: val for col, val in row.items()}

    async def _update_row(self, table, obj, **data):
        """ Generic method to update table row by object id. """
        col_vals = ',\n    '.join(f'{col} = {val}' for col, val in data.items())
        ret_vals = ',\n    '.join(data)
        statement = (
            f'UPDATE {table}\n'
            f'SET {col_vals}\n'
            'WHERE\n'
            '    id = $1\n'
            f'RETURNING {ret_vals};'
        )

        async with self.pool.acquire() as connection:
            async with connection.transaction():
                updated_vals = await connection.fetch(statement, obj.id)

        return {col: val for rec in updated_vals for col, val in rec.items()}

    async def insert_guilds(self, *guilds):
        """ Add a list of guilds into the guilds table and return the ones successfully added. """
        rows = [(guild.id, None, None, None) for guild in guilds]
        statement = (
            'INSERT INTO guilds (id)\n'
            '    (SELECT id FROM unnest($1::guilds[]))\n'
            '    ON CONFLICT (id) DO NOTHING\n'
            '    RETURNING id;'
        )

        async with self.pool.acquire() as connection:
            async with connection.transaction():
                inserted = await connection.fetch(statement, rows)

        return self._get_record_attrs(inserted, 'id')

    async def delete_guilds(self, *guilds):
        """ Remove a list of guilds from the guilds table and return the ones successfully removed. """
        delete_ids = [guild.id for guild in guilds]
        statement = (
            'DELETE FROM guilds\n'
            '    WHERE id::BIGINT = ANY($1::BIGINT[])\n'
            '    RETURNING id;'
        )

        async with self.pool.acquire() as connection:
            async with connection.transaction():
                deleted = await connection.fetch(statement, delete_ids)

        return self._get_record_attrs(deleted, 'id')

    async def sync_guilds(self, *guilds):
        """ Synchronizes the guilds table with the guilds in the bot. """
        insert_rows = [(guild.id, None, None, None) for guild in guilds]
        not_delete_ids = [guild.id for guild in guilds]
        insert_statement = (
            'INSERT INTO guilds (id)\n'
            '    (SELECT id FROM unnest($1::guilds[]))\n'
            '    ON CONFLICT (id) DO NOTHING\n'
            '    RETURNING id;'
        )
        delete_statement = (
            'DELETE FROM guilds\n'
            '    WHERE id::BIGINT != ALL($1::BIGINT[])\n'
            '    RETURNING id;'
        )

        async with self.pool.acquire() as connection:
            async with connection.transaction():
                inserted = await connection.fetch(insert_statement, insert_rows)
                deleted = await connection.fetch(delete_statement, not_delete_ids)

        return self._get_record_attrs(inserted, 'id'), self._get_record_attrs(deleted, 'id')

    async def insert_users(self, *users):
        """ Insert multiple users into the users table. """
        rows = [(user.id,) for user in users]
        statement = (
            'INSERT INTO users (id)\n'
            '    (SELECT id FROM unnest($1::users[]))\n'
            '    ON CONFLICT (id) DO NOTHING\n'
            '    RETURNING id;'
        )

        async with self.pool.acquire() as connection:
            async with connection.transaction():
                inserted = await connection.fetch(statement, rows)

        return self._get_record_attrs(inserted, 'id')

    async def delete_users(self, *users):
        """ Delete multiple users from the users table. """
        delete_ids = [user.id for user in users]
        statement = (
            'DELETE FROM users\n'
            '    WHERE id::BIGINT = ANY($1::BIGINT[])\n'
            '    RETURNING id;'
        )

        async with self.pool.acquire() as connection:
            async with connection.transaction():
                deleted = await connection.fetch(statement, delete_ids)

        return self._get_record_attrs(deleted, 'id')

    async def get_queued_users(self, guild):
        """ Get all the queued users of the guild from the queued_users table. """
        statement = (
            'SELECT\n'
            '    user_id\n'
            'FROM\n'
            '    queued_users\n'
            'WHERE\n'
            '    guild_id = $1;'
        )

        async with self.pool.acquire() as connection:
            async with connection.transaction():
                queue = await connection.fetch(statement, guild.id)

        return self._get_record_attrs(queue, 'user_id')

    async def insert_queued_users(self, guild, *users):
        """ Insert multiple users of a guild into the queued_users table. """
        statement = (
            'INSERT INTO queued_users (guild_id, user_id)\n'
            '    (SELECT * FROM unnest($1::queued_users[]));\n'
        )

        async with self.pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(statement, [(guild.id, user.id) for user in users])

    async def delete_queued_users(self, guild, *users):
        """ Delete multiple users of a guild from the queued_users table. """
        delete_ids = [user.id for user in users]
        statement = (
            'DELETE FROM queued_users\n'
            '    WHERE guild_id = $1 AND user_id = ANY($2::BIGINT[])'
            '    RETURNING user_id;'
        )

        async with self.pool.acquire() as connection:
            async with connection.transaction():
                deleted = await connection.fetch(statement, guild.id, delete_ids)

        return self._get_record_attrs(deleted, 'user_id')

    async def delete_all_queued_users(self, guild):
        """ Delete all users of a guild from the queued_users table. """
        statement = (
            'DELETE FROM queued_users\n'
            '    WHERE guild_id = $1'
            '    RETURNING user_id;'
        )

        async with self.pool.acquire() as connection:
            async with connection.transaction():
                deleted = await connection.fetch(statement, guild.id)

        return self._get_record_attrs(deleted, 'user_id')

    async def get_guild(self, guild):
        """ Get a guild's row from the guilds table. """
        return await self._get_row('guilds', guild)

    async def update_guild(self, guild, **data):
        """ Update a guild's row in the guilds table. """
        return await self._update_row('guilds', guild, **data)
