# api.py

import discord
from typing import List

from ...resources import Config, Sessions


class MatchServer:
    """
    Represents a match server with the contents returned by the API.
    """

    def __init__(self, id, ip, port):
        """ Set attributes. """
        self.id = match_id
        self.ip = ip
        self.port = port

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

        return f'connect {self.ip}:{self.port}'

    @property
    def match_page(self):
        """
        Generate the matches CS:GO League page link.
        """

        if Config.api_url:
            return f'{Config.api_url}/match/{self.id}'

    @classmethod
    async def new_match(cls, team_one: List[discord.User], team_two: List[discord.User], map_pick: str = None) -> 'MatchServer':
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
            json = await resp.json()
            return cls(**json)
