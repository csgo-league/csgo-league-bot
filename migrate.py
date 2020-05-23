# migrate.py

from dotenv import load_dotenv
from os import environ
import sys
from yoyo import get_backend, read_migrations


def migrate(direction):
    """ Apply Yoyo migrations for a given PostgreSQL database. """
    load_dotenv()
    connect_url = 'postgresql://{POSTGRESQL_USER}:{POSTGRESQL_PASSWORD}@{POSTGRESQL_HOST}/{POSTGRESQL_DB}'
    backend = get_backend(connect_url.format(**environ))
    migrations = read_migrations('./migrations')
    print('Applying migrations:\n' + '\n'.join(migration.id for migration in migrations))

    with backend.lock():
        if direction == 'up':
            backend.apply_migrations(backend.to_apply(migrations))
        elif direction == 'down':
            backend.rollback_migrations(backend.to_rollback(migrations))
        else:
            raise ValueError('Direction argument must be "up" or "down"')


if __name__ == '__main__':
    migrate(sys.argv[1])
