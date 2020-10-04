# api.py

import re
import aiohttp
import asyncio
import logging

from typing import AsyncGenerator

from .player import Player
from ..resources import Config, Sessions


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

    def __init__(self, json: dict):
        """
        Parameters
        ----------
        json : dict
        """

        self.id = json['match_id']
        self.ip = json['ip']
        self.port = json['port']

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

        if Config.api_url:
            return f'{Config.api_url}/match/{self.id}'


class User:
    def __init__(self, user_id: int) -> None:
        """

        Parameters
        ----------
        user_id : int
        """

        self.user_id = user_id

    async def generate_link_url(self) -> str:
        """Get custom URL from API for user to link accounts.

        Returns
        -------
        str
            Formatted link.
        """

        url = f'{Config.api_url}/discord/generate/{self.user_id}'

        async with Sessions.requests.get(url=url) as resp:
            resp_json = await resp.json()

            if "discord" in resp_json and "code" in resp_json:
                return f'{Config.api_url}/discord/{resp_json["discord"]}/{resp_json["code"]}'

    async def is_linked(self) -> bool:
        """
        Returns
        -------
        bool
        """

        url = f'{Config.api_url}/discord/check/{self.user_id}'

        async with Sessions.requests.get(url=url) as resp:
            resp_json = await resp.json()

            return resp_json["linked"] if "linked" in resp_json else False

    async def get_player(self) -> Player:
        """Get player data from the API.

        Returns
        -------
        Player
        """

        url = f'{Config.api_url}/player/discord/{self.user_id}'

        async with Sessions.requests.get(url=url) as resp:
            return Player(await resp.json())


async def update_discord_name(user: Player) -> bool:
    """Update a users API name to their current Discord display name.

    Parameters
    ----------
    user : Player

    Returns
    -------
    bool
    """

    url = f'{Config.api_url}/discord/update/{user.id}'
    data = {"discord_name": user.display_name}

    async with Sessions.requests.post(url=url, data=data) as resp:
        return resp.status == 200


async def get_players(user_ids: list) -> AsyncGenerator[Player, None]:
    """Get multiple players' data from the API.

    Parameters
    ----------
    user_ids : list

    Yields
    -------
    Player
    """

    url = f'{Config.api_url}/players/discord'
    discord_ids = {"discordIds": user_ids}

    async with Sessions.requests.post(url=url, json=discord_ids) as resp:
        players = await resp.json()

        players.sort(
            key=lambda x: user_ids.index(int(x['discord']))
        )  # Preserve order of user_ids arg

        for player in players:
            yield Player(player)


async def start_match(team_one: list, team_two: list, map_pick: str = None) -> MatchServer:
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

    url = f'{Config.api_url}/match/start'
    data = {
        'team_one': {user.id: user.display_name for user in team_one},
        'team_two': {user.id: user.display_name for user in team_two}
    }

    if map_pick:
        data['maps'] = map_pick

    async with Sessions.requests.post(url=url, json=data) as resp:
        return MatchServer(await resp.json())
