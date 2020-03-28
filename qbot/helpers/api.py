# api.py

import requests


class Match:
    def __init__(self, id, ip, port):
        self.id = id
        self.ip = ip
        self.port = port

    @property
    def connect_url(self):
        return f'steam://connect/{self.ip}:{self.port}'

    @property
    def connect_command(self):
        return f'connect {self.ip}:{self.port}'


class ApiHelper:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key

    @property
    def headers(self):
        return {'authentication': self.api_key}

    def generate_code(self, discord_id):
        url = f'{self.base_url}/discord/generate/{discord_id}'
        return requests.get(url=url, headers=self.headers)

    def is_linked(self, discord_id):
        url = f'{self.base_url}/discord/check/{discord_id}'
        response = requests.get(url=url, headers=self.headers)
        response = response.json()
        return response['linked']

    def update_discord_name(self, discord_id, discord_name):
        url = f'{self.base_url}/discord/update/{discord_id}'
        return requests.post(url=url, headers=self.headers, data={'discord_name': discord_name})

    def get_player(self, discord_id):
        url = f'{self.base_url}/player/discord/{discord_id}'
        return requests.get(url=url, headers=self.headers)

    def start_match(self, team_one, team_two):
        teams = {}
        teams['team_one'] = {user.id: user.display_name for user in team_one}
        teams['team_two'] = {user.id: user.display_name for user in team_two}
        response = requests.post(url=f'{self.base_url}/match/start', headers=self.headers, json=teams)
        json = response.json()
        return Match(json['match_id'], json['ip'], json['port']) if response.status_code == 200 else None
