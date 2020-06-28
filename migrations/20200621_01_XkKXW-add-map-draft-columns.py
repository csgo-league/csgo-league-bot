# 20200621_01_XkKXW-add-map-draft-columns.py

from yoyo import step

__depends__ = {'20200513_01_kPWNp-create-base-tables'}

steps = [
    step(
        'CREATE TYPE map_method AS ENUM(\'captains\', \'vote\', \'random\');',
        'DROP TYPE map_method;'
    ),
    step(
        (
            'ALTER TABLE guilds\n'
            'ADD COLUMN map_method map_method DEFAULT \'captains\';'
        ),
        (
            'ALTER TABLE guilds\n'
            'DROP COLUMN map_method;'
        )
    ),
    step(
        (
            'ALTER TABLE guilds\n'
            'ADD COLUMN de_cache BOOL NOT NULL DEFAULT true,\n'
            'ADD COLUMN de_cbble BOOL NOT NULL DEFAULT true,\n'
            'ADD COLUMN de_dust2 BOOL NOT NULL DEFAULT true,\n'
            'ADD COLUMN de_mirage BOOL NOT NULL DEFAULT true,\n'
            'ADD COLUMN de_overpass BOOL NOT NULL DEFAULT true,\n'
            'ADD COLUMN de_nuke BOOL NOT NULL DEFAULT true,\n'
            'ADD COLUMN de_inferno BOOL NOT NULL DEFAULT true,\n'
            'ADD COLUMN de_train BOOL NOT NULL DEFAULT true,\n'
            'ADD COLUMN de_vertigo BOOL NOT NULL DEFAULT true;'
        ),
        (
            'ALTER TABLE guilds\n'
            'DROP COLUMN de_cache,\n'
            'DROP COLUMN de_cbble,\n'
            'DROP COLUMN de_dust2,\n'
            'DROP COLUMN de_mirage,\n'
            'DROP COLUMN de_overpass,\n'
            'DROP COLUMN de_nuke,\n'
            'DROP COLUMN de_inferno,\n'
            'DROP COLUMN de_train,\n'
            'DROP COLUMN de_vertigo;'
        )
    )
]
