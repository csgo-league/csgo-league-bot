# migration.py

import asyncpg


async def get_db(**credentials):
    db = await asyncpg.create_pool(**credentials)
    await migrate(db)
    return db

async def migrate(db):
    """"""
    retval = await db.execute('''
            CREATE TABLE IF NOT EXISTS guilds(
                id serial PRIMARY KEY,
                capacity smallint DEFAULT 10,
                auto_balance bool DEFAULT false
            )
        ''')
