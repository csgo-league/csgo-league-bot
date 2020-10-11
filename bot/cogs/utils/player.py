# player.py

import discord
from typing import AsyncGenerator, List

from ...resources import Config, Sessions


def catch_ZeroDivisionError(func):
    """ Decorator to catch ZeroDivisionError and return 0. """
    def caught_func(*args, **kwargs):
        """ Function to be returned by the decorator. """
        try:
            return func(*args, **kwargs)
        except ZeroDivisionError:
            return 0

    return caught_func


class PlayerStats:
    """ Represents a player with the contents returned by the API. """

    def __init__(self, player_data):
        """ Set attributes. """

        # This will be faster then looping over self.__dict__
        # and calling setattr a bunch of times.
        for key, value in player_data.items():
            if type(value) != str:
                player_data[key] = 0 if value is None else int(value)

        self.steam = player_data['steam']
        self.discord = player_data['discord']
        self.discord_name = player_data['discord_name']
        self.id = player_data['id']
        self.score = player_data['score']
        self.kills = player_data['kills']
        self.deaths = player_data['deaths']
        self.assists = player_data['assists']
        self.suicides = player_data['suicides']
        self.tk = player_data['tk']
        self.shots = player_data['shots']
        self.hits = player_data['hits']
        self.headshots = player_data['headshots']
        self.connected = player_data['connected']
        self.rounds_tr = player_data['rounds_tr']
        self.rounds_ct = player_data['rounds_ct']
        self.lastconnect = player_data['lastconnect']
        self.knife = player_data['knife']
        self.glock = player_data['glock']
        self.hkp2000 = player_data['hkp2000']
        self.usp_silencer = player_data['usp_silencer']
        self.p250 = player_data['p250']
        self.deagle = player_data['deagle']
        self.elite = player_data['elite']
        self.fiveseven = player_data['fiveseven']
        self.tec9 = player_data['tec9']
        self.cz75a = player_data['cz75a']
        self.revolver = player_data['revolver']
        self.nova = player_data['nova']
        self.xm1014 = player_data['xm1014']
        self.mag7 = player_data['mag7']
        self.sawedoff = player_data['sawedoff']
        self.bizon = player_data['bizon']
        self.mac10 = player_data['mac10']
        self.mp9 = player_data['mp9']
        self.mp7 = player_data['mp7']
        self.ump45 = player_data['ump45']
        self.p90 = player_data['p90']
        self.galilar = player_data['galilar']
        self.ak47 = player_data['ak47']
        self.scar20 = player_data['scar20']
        self.famas = player_data['famas']
        self.m4a1 = player_data['m4a1']
        self.m4a1_silencer = player_data['m4a1_silencer']
        self.aug = player_data['aug']
        self.ssg08 = player_data['ssg08']
        self.sg556 = player_data['sg556']
        self.awp = player_data['awp']
        self.g3sg1 = player_data['g3sg1']
        self.m249 = player_data['m249']
        self.negev = player_data['negev']
        self.hegrenade = player_data['hegrenade']
        self.flashbang = player_data['flashbang']
        self.smokegrenade = player_data['smokegrenade']
        self.inferno = player_data['inferno']
        self.decoy = player_data['decoy']
        self.taser = player_data['taser']
        self.mp5sd = player_data['mp5sd']
        self.breachcharge = player_data['breachcharge']
        self.head = player_data['head']
        self.chest = player_data['chest']
        self.stomach = player_data['stomach']
        self.left_arm = player_data['left_arm']
        self.right_arm = player_data['right_arm']
        self.left_leg = player_data['left_leg']
        self.right_leg = player_data['right_leg']
        self.c4_planted = player_data['c4_planted']
        self.c4_exploded = player_data['c4_exploded']
        self.c4_defused = player_data['c4_defused']
        self.ct_win = player_data['ct_win']
        self.tr_win = player_data['tr_win']
        self.hostages_rescued = player_data['hostages_rescued']
        self.vip_killed = player_data['vip_killed']
        self.vip_escaped = player_data['vip_escaped']
        self.vip_played = player_data['vip_played']
        self.mvp = player_data['mvp']
        self.damage = player_data['damage']
        self.match_win = player_data['match_win']
        self.match_draw = player_data['match_draw']
        self.match_lose = player_data['match_lose']
        self.first_blood = player_data['first_blood']
        self.no_scope = player_data['no_scope']
        self.no_scope_dis = player_data['no_scope_dis']
        self.in_match = player_data['inMatch']

    @property
    def league_profile(self):
        """ Generate the player's CS:GO League profile link. """
        if Config.api_url:
            return f'{Config.api_url}/profile/{self.steam}'

    @property
    def steam_profile(self):
        """ Generate the player's Steam profile link. """
        return f'https://steamcommunity.com/profiles/{self.steam}'

    @property
    def matches_played(self):
        """ Calculate and return matches played. """
        return self.match_win + self.match_draw + self.match_lose

    @property
    @catch_ZeroDivisionError
    def win_percent(self):
        """ Calculate and return win percentage. """
        return self.match_win / (self.match_win + self.match_lose)

    @property
    @catch_ZeroDivisionError
    def kd_ratio(self):
        """ Calculate and return K/D ratio. """
        return self.kills / self.deaths

    @property
    @catch_ZeroDivisionError
    def adr(self):
        """ Calculate and return average damage per round. """
        return self.damage / (self.rounds_tr + self.rounds_ct)

    @property
    @catch_ZeroDivisionError
    def hs_percent(self):
        """ Calculate and return headshot kill percentage. """
        return float(self.headshots / self.kills)

    @property
    @catch_ZeroDivisionError
    def first_blood_rate(self):
        return self.first_blood / (self.rounds_tr + self.rounds_ct)

    @classmethod
    async def from_id(cls, discord_id: int):
        """Get player data from their Discord user ID.

        Parameters
        ----------
        discord_id : int

        Returns
        -------
        PlayerStats
        """

        url = f'{Config.api_url}/player/discord/{discord_id}'

        async with Sessions.requests.get(url=url) as resp:
            return cls(await resp.json())

    @classmethod
    async def from_ids(cls, discord_ids: List[int]) -> AsyncGenerator['PlayerStats', None]:
        """Get multiple players' data from their Discord user IDs.

        Parameters
        ----------
        discord_ids : List[int]

        Yields
        -------
        PlayerStats
        """

        url = f'{Config.api_url}/players/discord'
        discord_ids = {"discordIds": discord_ids}

        async with Sessions.requests.post(url=url, json=discord_ids) as resp:
            players = await resp.json()

            players.sort(
                key=lambda x: discord_ids.index(int(x['discord']))
            )  # Preserve order of discord_ids arg

            for player in players:
                yield cls(player)


class Player:
    def __init__(self, discord_id: int) -> None:
        """

        Parameters
        ----------
        discord_id : int
        """

        self.discord_id = discord_id

    async def generate_link_url(self) -> str:
        """Get custom URL from API for user to link accounts.

        Returns
        -------
        str
            Formatted link.
        """

        url = f'{Config.api_url}/discord/generate/{self.discord_id}'

        async with Sessions.requests.get(url=url) as resp:
            resp_json = await resp.json()

            if 'discord' in resp_json and 'code' in resp_json:
                return f'{Config.api_url}/discord/{resp_json["discord"]}/{resp_json["code"]}'

    async def is_linked(self) -> bool:
        """
        Returns
        -------
        bool
        """

        url = f'{Config.api_url}/discord/check/{self.discord_id}'

        async with Sessions.requests.get(url=url) as resp:
            resp_json = await resp.json()

            return resp_json["linked"] if "linked" in resp_json else False

    async def get_stats(self) -> PlayerStats:
        """Get player data from the API.

        Returns
        -------
        PlayerStats
        """

        return PlayerStats.from_id(self.discord_id)


async def update_discord_name(user: discord.User) -> bool:
    """Update a users API name to their current Discord display name.

    Parameters
    ----------
    user : discord.User

    Returns
    -------
    bool
    """

    url = f'{Config.api_url}/discord/update/{user.id}'
    data = {'discord_name': user.display_name}

    async with Sessions.requests.post(url=url, data=data) as resp:
        return resp.status == 200
