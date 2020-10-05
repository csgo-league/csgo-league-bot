# api.py

import aiohttp
import asyncio
import json
import logging

from .player import Player


class MatchServer:
    """ Represents a match server with the contents returned by the API. """

    def __init__(self, id, ip, port, web_url=None):
        """ Set attributes. """
        self.id = match_id
        self.ip = ip
        self.port = port
        self.web_url = web_url

    @property
    def connect_url(self):
        """ Format URL to connect to server. """
        return f'steam://connect/{self.ip}:{self.port}'

    @property
    def connect_command(self):
        """ Format console command to connect to server. """
        return f'connect {self.ip}:{self.port}'

    @property
    def match_page(self):
        """ Generate the matches CS:GO League page link. """
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


class ApiWrapper:
    """ Class to contain API request wrapper functions. """

    def __init__(self, loop, base_url, api_key):
        """ Set attributes and initialize logging handlers. """
        # Set attributes
        self.base_url = base_url
        self.api_key = api_key
        self.logger = logging.getLogger('csgoleague.api')

        # Check API URL
        if not self.base_url.startswith('https') and self.base_url.startswith('http'):
            self.logger.warning(f'API url "{self.base_url}" should start with "https" instead of "http"')

        # Register trace config handlers
        trace_config = aiohttp.TraceConfig()
        trace_config.on_request_start.append(start_request_log)
        trace_config.on_request_end.append(end_request_log)

        # Start session
        self.logger.info('Starting API helper client session')
        self.session = aiohttp.ClientSession(loop=loop, json_serialize=lambda x: json.dumps(x, ensure_ascii=False),
                                             raise_for_status=True, trace_configs=[trace_config])

    async def close(self):
        """ Close the API helper's session. """
        self.logger.info('Closing API helper client session')
        await self.session.close()

    @property
    def headers(self):
        """ Default authentication header the API needs. """
        return {'authentication': self.api_key}

    async def generate_link_url(self, user_id):
        """ Get custom URL from API for user to link accounts. """
        url = f'{self.base_url}/discord/generate/{user_id}'

        async with self.session.get(url=url, headers=self.headers) as resp:
            resp_json = await resp.json()

            if resp_json.get('discord') and resp_json.get('code'):
                return f'{self.base_url}/discord/{resp_json["discord"]}/{resp_json["code"]}'

    async def is_linked(self, user_id):
        """ Check if a user has their account linked with the API. """
        url = f'{self.base_url}/discord/check/{user_id}'

        async with self.session.get(url=url, headers=self.headers) as resp:
            resp_json = await resp.json()

            if resp_json.get('linked'):
                return resp_json['linked']
            else:
                return False

    async def update_discord_name(self, user):
        """ Update a users API name to their current Discord display name. """
        url = f'{self.base_url}/discord/update/{user.id}'
        data = {'discord_name': user.display_name}

        async with self.session.post(url=url, headers=self.headers, data=data) as resp:
            return resp.status == 200

    async def get_player(self, user_id):
        """ Get player data from the API. """
        url = f'{self.base_url}/player/discord/{user_id}'

        async with self.session.get(url=url, headers=self.headers) as resp:
            return Player(await resp.json(), self.base_url)

    async def get_players(self, user_ids):
        """ Get multiple players' data from the API. """
        url = f'{self.base_url}/players/discord'
        discord_ids = {"discordIds": user_ids}

        async with self.session.post(url=url, headers=self.headers, json=discord_ids) as resp:
            players = await resp.json()
            players.sort(key=lambda x: user_ids.index(int(x['discord'])))  # Preserve order of user_ids arg
            return [Player(player_data, self.base_url) for player_data in players]

    async def start_match(self, team_one, team_two, map_pick=None):
        """ Get a match server from the API. """
        url = f'{self.base_url}/match/start'
        data = {
            'team_one': {user.id: user.display_name for user in team_one},
            'team_two': {user.id: user.display_name for user in team_two}
        }

        if map_pick:
            data['maps'] = map_pick

        async with self.session.post(url=url, headers=self.headers, json=data) as resp:
            resp = await resp.json()

        return MatchServer(**resp, web_url=self.base_url)
