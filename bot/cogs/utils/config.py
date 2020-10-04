# config.py

import enum

from .map import MapPool


class ConfigMethod(enum.Enum):
    """
    Base class for config method enums.
    """

    @classmethod
    def from_str(cls, option: str) -> int:
        """Get the config method enum from a lowercase string.

        Parameters
        ----------
        option : str
        """
        return getattr(cls, option.lower)


class TeamMethod(ConfigMethod):
    """
    Enum for options by which to decide teams.
    """
    CAPTAINS = enum.auto()
    AUTOBALANCE = enum.auto()
    RANDOM = enum.auto()


class CaptainMethod(ConfigMethod):
    """
    Enum for options by which to decide captains.
    """
    VOLUNTEER = enum.auto()
    RANK = enum.auto()
    RANDOM = enum.auto()


class MapMethod(ConfigMethod):
    """
    Enum for options by which to decide the map.
    """
    CAPTAINS = enum.auto()
    VOTE = enum.auto()
    RANDOM = enum.auto()


class GuildConfig:
    """
    Holds all of a guild's settings saved in the database.
    """

    def __init__(self, capacity: int, team_method: int, captain_method: int, map_method: int, map_pool: MapPool) -> GuildConfig:
        self.capacity = capacity
        self.team_method = team_method
        self.captain_method = captain_method
        self.map_method = map_method
        self.map_pool = map_pool

    @classmethod
    def from_dict(cls, config: dict) -> GuildConfig:
        """"""
        return cls(config['capacity'],
                   TeamMethod.from_str(config['team_method']),
                   CaptainMethod.from_str(config['captain_method']),
                   MapMethod.from_str(config['map_method']),
                   MapPool.from_dict(config))
