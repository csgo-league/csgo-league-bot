# config.py

import enum

from .map import MapPool


class _ConfigMethod(enum.Enum):
    """
    Base class for config method enums.
    """

    def __str__(self):
        return self.name.lower()

    @classmethod
    def enum_str(cls, name: str) -> int:
        """Get the config method enum from a string (case insensitive).

        Parameters
        ----------
        name : str
            Lowercase name of the enum to get.

        Raises
        ------
        AttributeError
            Class attribute doesn't exist.

        Returns
        -------
        int
            The found enum value.
        """
        return getattr(cls, name.upper())


class TeamMethod(_ConfigMethod):
    """
    Enum for options by which to decide teams.
    """
    CAPTAINS = enum.auto()
    AUTOBALANCE = enum.auto()
    RANDOM = enum.auto()


class CaptainMethod(_ConfigMethod):
    """
    Enum for options by which to decide captains.
    """
    VOLUNTEER = enum.auto()
    RANK = enum.auto()
    RANDOM = enum.auto()


class MapMethod(_ConfigMethod):
    """
    Enum for options by which to decide the map.
    """
    CAPTAINS = enum.auto()
    VOTE = enum.auto()
    RANDOM = enum.auto()


class GuildConfig:
    """Holds all of a guild's settings saved in the database.

    Attributes
    ----------
    capacity : int
        Maximum queue size before popping to start a match.
    team_method : int
        Enum indicating the method by which teams are chosen. Specify this
        argument using the values in the TeamMethod class.
    captain_method : int
        Enum indicating the method by which captains are chosen. Same as
        team_method but for the CaptainMethod class.
    map_method : int
        Enum indicating the method by which the map is chosen. Same as
        team_method but for the MapMethod class.
    map_pool : MapPool
        The guild's map pool.
    """

    def __init__(self, capacity: int, team_method: int, captain_method: int, map_method: int, map_pool: MapPool):
        self.capacity = capacity
        self.team_method = team_method
        self.captain_method = captain_method
        self.map_method = map_method
        self.map_pool = map_pool

    @classmethod
    def from_dict(cls, guild_data: dict):
        """Create a GuildConfig from a dictionary as returned by the database.

        Parameters
        ----------
        guild_data : dict
            Dictionary with guild config information from the database.

        Returns
        -------
        GuildData
            A new GuildData object.
        """
        return cls(guild_data['capacity'],
                   TeamMethod.enum_str(guild_data['team_method']),
                   CaptainMethod.enum_str(guild_data['captain_method']),
                   MapMethod.enum_str(guild_data['map_method']),
                   MapPool.from_dict(guild_data))

    @property
    def to_dict(self):
        """Convert object to a dictionary format to match the database entry.

        Returns
        -------
        dict
            Dictionary containing the config data formatted for the database.
        """
        guild_data = {
            'capacity': self.capacity,
            'team_method': TeamMethod(self.team_method).name.lower,
            'captain_method': CaptainMethod(self.captain_method).name.lower,
            'map_method': MapMethod(self.map_method).name.lower
        }
        guild_data.update(self.map_pool.to_dict)
        return guild_data
