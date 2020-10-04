# api.py

import aiohttp
import asyncio
import json
import logging

from typing import AsyncGenerator

from .player import Player


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

        return f'steam://connect/{self.ip}:{self.port}'

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
            return f'{self.web_url}/match/{self.id}'


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

        url = f'{self.base_url}/discord/generate/{user_id}'

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

        url = f'{self.base_url}/discord/check/{user_id}'

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

        url = f'{self.base_url}/discord/update/{user.id}'
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

        url = f'{self.base_url}/player/discord/{user_id}'

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

        url = f'{self.base_url}/players/discord'
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

        url = f'{self.base_url}/match/start'
        data = {
            'team_one': {user.id: user.display_name for user in team_one},
            'team_two': {user.id: user.display_name for user in team_two}
        }

        if map_pick:
            data['maps'] = map_pick

        async with self.session.post(url=url, json=data) as resp:
            return MatchServer(await resp.json(), self.base_url)
