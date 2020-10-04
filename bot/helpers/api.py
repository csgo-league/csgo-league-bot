# api.py

import aiohttp
import asyncio
import json
import logging

from typing import AsyncGenerator


def catch_ZeroDivisionError(func):
    """
    Decorator to catch ZeroDivisionError and return 0.
    """

    def caught_func(*args, **kwargs):
        """
        Function to be returned by the decorator.
        """

        try:
            return func(*args, **kwargs)
        except ZeroDivisionError:
            return 0

    return caught_func


class Player:
    """
    Represents a player with the contents returned by the API.
    """

    def __init__(self, player_data: dict, web_url: str = None) -> None:
        """
        Parameters
        ----------
        player_data : dict
        web_url : str, optional
            by default None
        """

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

        self.web_url = web_url

    @property
    def league_profile(self) -> str:
        """
        Generate the player's CS:GO League profile link.
        """

        if self.web_url:
            return "{}/profile/{}".format(self.web_url, self.steam)

    @property
    def steam_profile(self) -> str:
        """
        Generate the player's Steam profile link.
        """

        return "https://steamcommunity.com/profiles/{}".format(self.steam)

    @property
    def matches_played(self) -> int:
        """
        Calculate and return matches played.
        """

        return self.match_win + self.match_draw + self.match_lose

    @property
    @catch_ZeroDivisionError
    def win_percent(self) -> float:
        """
        Calculate and return win percentage.
        """

        return self.match_win / (self.match_win + self.match_lose)

    @property
    @catch_ZeroDivisionError
    def kd_ratio(self) -> float:
        """
        Calculate and return K/D ratio.
        """

        return self.kills / self.deaths

    @property
    @catch_ZeroDivisionError
    def adr(self) -> float:
        """
        Calculate and return average damage per round.
        """

        return self.damage / (self.rounds_tr + self.rounds_ct)

    @property
    @catch_ZeroDivisionError
    def hs_percent(self) -> float:
        """
        Calculate and return headshot kill percentage.
        """

        return float(self.headshots / self.kills)

    @property
    @catch_ZeroDivisionError
    def first_blood_rate(self) -> None:

        return self.first_blood / (self.rounds_tr + self.rounds_ct)


class MatchServer:
    """
    Represents a match server with the contents returned by the API.
    """

    def __init__(self, json: dict, web_url: str = None):
        """
        Parameters
        ----------
        json : dict
        web_url : str, optional
            by default None
        """

        self.id = json['match_id']
        self.ip = json['ip']
        self.port = json['port']
        self.web_url = web_url

    @property
    def connect_url(self):
        """
        Format URL to connect to server.
        """

        return "steam://connect/{}:{}".format(self.ip, self.port)

    @property
    def connect_command(self):
        """
        Format console command to connect to server.
        """

        return "connect {}:{}".format(self.ip, self.port)

    @property
    def match_page(self):
        """
        Generate the matches CS:GO League page link.
        """

        if self.web_url:
            return "{}/match/{}".format(self.web_url, self.id)


async def start_request_log(session, ctx, params):
    """"""

    ctx.start = asyncio.get_event_loop().time()
    logger = logging.getLogger('csgoleague.api')
    logger.info(f'Sending {params.method} request to {params.url}')


async def end_request_log(session, ctx, params):
    """"""

    logger = logging.getLogger('csgoleague.api')
    elapsed = asyncio.get_event_loop().time() - ctx.start
    logger.info(f'Response received from {params.url} ({elapsed:.2f}s)\n'
                f'    Status: {params.response.status}\n'
                f'    Reason: {params.response.reason}')
    resp_json = await params.response.json()
    logger.debug(f'Response JSON from {params.url}: {resp_json}')


class ApiHelper:
    """ Class to contain API request wrapper functions. """

    def __init__(self, loop, base_url: str, api_key: str) -> None:
        """Set attributes and initialize logging handlers.

        Parameters
        ----------
        loop
        base_url : str
        api_key : str
        """

        self.base_url = base_url
        self.api_key = api_key
        self.logger = logging.getLogger('csgoleague.api')

        # Check API URL
        if not self.base_url.startswith('https') \
                and self.base_url.startswith('http'):

            self.logger.warning(
                "API url '{}' should start with 'https' instead of 'http'"
                .format(self.base_url)
            )

        # Register trace config handlers
        trace_config = aiohttp.TraceConfig()
        trace_config.on_request_start.append(start_request_log)
        trace_config.on_request_end.append(end_request_log)

        # Start session
        self.logger.info('Starting API helper client session')
        self.session = aiohttp.ClientSession(
            loop=loop, json_serialize=lambda x: json.dumps(
                x, ensure_ascii=False),
            raise_for_status=True,
            trace_configs=[trace_config],
            headers={"authentication": self.api_key}
        )

    async def close(self) -> None:
        """
        Close the API helper's session.
        """

        self.logger.info('Closing API helper client session')
        await self.session.close()

    async def generate_link_url(self, user_id: int) -> str:
        """Get custom URL from API for user to link accounts.

        Parameters
        ----------
        user_id : int

        Returns
        -------
        str
            Formatted link.
        """

        url = "{}/discord/generate/{}".format(self.base_url, user_id)

        async with self.session.get(url=url) as resp:
            resp_json = await resp.json()

            if "discord" in resp_json and "code" in resp_json:
                return "{}/discord/{}/{}".format(
                    self.base_url, resp_json["discord"], resp_json["code"])

    async def is_linked(self, user_id: int) -> bool:
        """
        Parameters
        ----------
        user_id : int

        Returns
        -------
        bool
        """

        url = "{}/discord/check/{}".format(self.base_url, user_id)

        async with self.session.get(url=url) as resp:
            resp_json = await resp.json()

            return resp_json["linked"] if "linked" in resp_json else False

    async def update_discord_name(self, user: Player) -> bool:
        """Update a users API name to their current Discord display name.

        Parameters
        ----------
        user : Player

        Returns
        -------
        bool
        """

        url = "{}/discord/update/{}".format(self.base_url, user.id)
        data = {"discord_name": user.display_name}

        async with self.session.post(url=url, data=data) as resp:
            return resp.status == 200

    async def get_player(self, user_id: int) -> Player:
        """Get player data from the API.

        Parameters
        ----------
        user_id : int

        Returns
        -------
        Player
        """

        url = "{}/player/discord/{}".format(self.base_url, user_id)

        async with self.session.get(url=url) as resp:
            return Player(await resp.json(), self.base_url)

    async def get_players(self, user_ids: list
                          ) -> AsyncGenerator[Player, None]:
        """Get multiple players' data from the API.

        Parameters
        ----------
        user_ids : list

        Yields
        -------
        Player
        """

        url = "{}/players/discord".format(self.base_url)
        discord_ids = {"discordIds": user_ids}

        async with self.session.post(url=url, json=discord_ids) as resp:
            players = await resp.json()

            players.sort(
                key=lambda x: user_ids.index(int(x['discord']))
            )  # Preserve order of user_ids arg

            for player in players:
                yield Player(player, self.base_url)

    async def start_match(self, team_one: list,
                          team_two: list, map_pick: str = None) -> MatchServer:
        """Get a match server from the API.

        Parameters
        ----------
        team_one : list
        team_two : list
        map_pick : str, optional
            by default None

        Returns
        -------
        MatchServer
        """

        url = "{}/match/start".format(self.base_url)
        data = {
            "team_one": {user.id: user.display_name for user in team_one},
            "team_two": {user.id: user.display_name for user in team_two}
        }

        if map_pick:
            data['maps'] = map_pick

        async with self.session.post(url=url, json=data) as resp:
            return MatchServer(await resp.json(), self.base_url)
