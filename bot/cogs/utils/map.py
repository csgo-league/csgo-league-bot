# map.py


class Map:
    """ A group of attributes representing a map. """
    image_folder = 'https://raw.githubusercontent.com/csgo-league/csgo-league-bot/develop/assets/maps/images/'
    icon_folder = 'https://raw.githubusercontent.com/csgo-league/csgo-league-bot/develop/assets/maps/icons/'

    def __init__(self, name, dev_name):
        """ Set attributes. """
        self.name = name
        self.dev_name = dev_name

    @property
    def image_url(self):
        return f'{self.image_folder}{self.dev_name}.jpg'

    @property
    def icon_url(self):
        return f'{self.icon_folder}{self.dev_name}.png'


class Maps:
    """
    Namespace to store all maps under.
    """
    de_ancient = Map('Ancient', 'de_ancient')
    de_cache = Map('Cache', 'de_cache')
    de_cbble = Map('Cobblestone', 'de_cbble')
    de_dust2 = Map('Dust II', 'de_dust2')
    de_inferno = Map('Inferno', 'de_inferno')
    de_mirage = Map('Mirage', 'de_mirage')
    de_nuke = Map('Nuke', 'de_nuke')
    de_overpass = Map('Overpass', 'de_overpass')
    de_train = Map('Train', 'de_train')
    de_vertigo = Map('Vertigo', 'de_vertigo')
    all = {de_ancient, de_cache, de_cbble, de_dust2, de_inferno, de_mirage, de_nuke, de_overpass, de_train, de_vertigo}


class MapPool(set):
    """"""

    @classmethod
    def from_dict(cls, map_dict):
        """ Get map pool from dict of dev name to boolean. """
        return cls((m for m in Maps.all if map_dict[m.dev_name]))

    @property
    def to_dict(self):
        """Convert object to a dictionary format to match the database entry.

        Returns
        -------
        dict
            Dictionary containing the map pool data formatted for the database.
        """
        return {m.dev_name: m in self for m in Maps.all}
