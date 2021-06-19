"""
Add map de_ancient
"""

from yoyo import step

__depends__ = {'20200621_01_XkKXW-add-map-draft-columns'}

steps = [
    step(
        (
            'ALTER TABLE guilds\n',
            'ADD COLUMN de_ancient BOOL NOT NULL DEFAULT true;'
        ),
        (
            'ALTER TABLE guilds\n',
            'DROP COLUMN de_ancient;'
        )
    )
]
