# api.py


class Player:
    """ Represents a player with the contents returned by the API. """

    def __init__(self, player_data):
        """ Set attributes. """
        self.steam = int(player_data['steam'])
        self.discord = int(player_data['discord'])
        self.discord_name = str(player_data['discord_name'])
        self.id = int(player_data['id'])
        self.score = int(player_data['score'])
        self.kills = int(player_data['kills'])
        self.deaths = int(player_data['deaths'])
        self.assists = int(player_data['assists'])
        self.suicides = int(player_data['suicides'])
        self.tk = int(player_data['tk'])
        self.shots = int(player_data['shots'])
        self.hits = int(player_data['hits'])
        self.headshots = int(player_data['headshots'])
        self.connected = int(player_data['connected'])
        self.rounds_tr = int(player_data['rounds_tr'])
        self.rounds_ct = int(player_data['rounds_ct'])
        self.lastconnect = int(player_data['lastconnect'])
        self.knife = int(player_data['knife'])
        self.glock = int(player_data['glock'])
        self.hkp2000 = int(player_data['hkp2000'])
        self.usp_silencer = int(player_data['usp_silencer'])
        self.p250 = int(player_data['p250'])
        self.deagle = int(player_data['deagle'])
        self.elite = int(player_data['elite'])
        self.fiveseven = int(player_data['fiveseven'])
        self.tec9 = int(player_data['tec9'])
        self.cz75a = int(player_data['cz75a'])
        self.revolver = int(player_data['revolver'])
        self.nova = int(player_data['nova'])
        self.xm1014 = int(player_data['xm1014'])
        self.mag7 = int(player_data['mag7'])
        self.sawedoff = int(player_data['sawedoff'])
        self.bizon = int(player_data['bizon'])
        self.mac10 = int(player_data['mac10'])
        self.mp9 = int(player_data['mp9'])
        self.mp7 = int(player_data['mp7'])
        self.ump45 = int(player_data['ump45'])
        self.p90 = int(player_data['p90'])
        self.galilar = int(player_data['galilar'])
        self.ak47 = int(player_data['ak47'])
        self.scar20 = int(player_data['scar20'])
        self.famas = int(player_data['famas'])
        self.m4a1 = int(player_data['m4a1'])
        self.m4a1_silencer = int(player_data['m4a1_silencer'])
        self.aug = int(player_data['aug'])
        self.ssg08 = int(player_data['ssg08'])
        self.sg556 = int(player_data['sg556'])
        self.awp = int(player_data['awp'])
        self.g3sg1 = int(player_data['g3sg1'])
        self.m249 = int(player_data['m249'])
        self.negev = int(player_data['negev'])
        self.hegrenade = int(player_data['hegrenade'])
        self.flashbang = int(player_data['flashbang'])
        self.smokegrenade = int(player_data['smokegrenade'])
        self.inferno = int(player_data['inferno'])
        self.decoy = int(player_data['decoy'])
        self.taser = int(player_data['taser'])
        self.mp5sd = int(player_data['mp5sd'])
        self.breachcharge = int(player_data['breachcharge'])
        self.head = int(player_data['head'])
        self.chest = int(player_data['chest'])
        self.stomach = int(player_data['stomach'])
        self.left_arm = int(player_data['left_arm'])
        self.right_arm = int(player_data['right_arm'])
        self.left_leg = int(player_data['left_leg'])
        self.right_leg = int(player_data['right_leg'])
        self.c4_planted = int(player_data['c4_planted'])
        self.c4_exploded = int(player_data['c4_exploded'])
        self.c4_defused = int(player_data['c4_defused'])
        self.ct_win = int(player_data['ct_win'])
        self.tr_win = int(player_data['tr_win'])
        self.hostages_rescued = int(player_data['hostages_rescued'])
        self.vip_killed = int(player_data['vip_killed'])
        self.vip_escaped = int(player_data['vip_escaped'])
        self.vip_played = int(player_data['vip_played'])
        self.mvp = int(player_data['mvp'])
        self.damage = int(player_data['damage'])
        self.match_win = int(player_data['match_win'])
        self.match_draw = int(player_data['match_draw'])
        self.match_lose = int(player_data['match_lose'])
        self.first_blood = int(player_data['first_blood'])
        self.no_scope = int(player_data['no_scope'])
        self.no_scope_dis = int(player_data['no_scope_dis'])
        self.in_match = bool(player_data['inMatch'])

    @property
    def steam_profile(self):
        """ Generate the player's Steam profile link. """
        return f'https://steamcommunity.com/profiles/{self.steam}'

    @property
    def matches_played(self):
        """ Calculate and return matches played. """
        return self.match_win + self.match_draw + self.match_lose

    @property
    def win_percent(self):
        """ Calculate and return win percentage. """
        try:
            return self.match_win / (self.match_win + self.match_lose)
        except ZeroDivisionError:
            return 0

    @property
    def kd_ratio(self):
        """ Calculate and return K/D ratio. """
        try:
            return self.kills / self.deaths
        except ZeroDivisionError:
            return 0

    @property
    def adr(self):
        """ Calculate and return average damage per round. """
        try:
            return self.damage / (self.rounds_tr + self.rounds_ct)
        except ZeroDivisionError:
            return 0

    @property
    def hs_percent(self):
        """ Calculate and return headshot kill percentage. """
        try:
            return float(self.headshots / self.kills)
        except ZeroDivisionError:
            return 0

    @property
    def first_blood_rate(self):
        try:
            return self.first_blood / (self.rounds_tr + self.rounds_ct)
        except ZeroDivisionError:
            return 0


class MatchServer:
    """ Represents a match server with the contents returned by the API. """

    def __init__(self, json):
        """ Set attributes. """
        self.id = json['match_id']
        self.ip = json['ip']
        self.port = json['port']

    @property
    def connect_url(self):
        """ Format URL to connect to server. """
        return f'steam://connect/{self.ip}:{self.port}'

    @property
    def connect_command(self):
        """ Format console command to connect to server. """
        return f'connect {self.ip}:{self.port}'


class ApiHelper:
    """ Class to contain API request wrapper functions. """

    def __init__(self, session, base_url, api_key):
        """ Set attributes. """
        self.session = session
        self.base_url = base_url
        self.api_key = api_key

    @property
    def headers(self):
        """ Default authentication header the API needs. """
        return {'authentication': self.api_key}

    async def generate_link_url(self, user):
        """ Get custom URL from API for user to link accounts. """
        url = f'{self.base_url}/discord/generate/{user.id}'

        async with self.session.get(url=url, headers=self.headers) as resp:
            resp.raise_for_status()

            if resp.status == 200:
                resp_json = await resp.json()

                if resp_json.get('discord') and resp_json.get('code'):
                    return f'{self.base_url}/discord/{resp_json["discord"]}/{resp_json["code"]}'

    async def is_linked(self, user):
        """ Check if a user has their account linked with the API. """
        url = f'{self.base_url}/discord/check/{user.id}'

        async with self.session.get(url=url, headers=self.headers) as resp:
            resp.raise_for_status()

            if resp.status == 200:
                resp_json = await resp.json()

                if resp_json.get('linked'):
                    return resp_json['linked']

    async def update_discord_name(self, user):
        """ Update a users API name to their current Discord display name. """
        url = f'{self.base_url}/discord/update/{user.id}'
        data = {'discord_name': user.display_name}

        async with self.session.post(url=url, headers=self.headers, data=data) as resp:
            resp.raise_for_status()
            return resp.status == 200

    async def get_player(self, user):
        """ Get player data from the API. """
        url = f'{self.base_url}/player/discord/{user.id}'

        async with self.session.get(url=url, headers=self.headers) as resp:
            resp.raise_for_status()

            if resp.status == 200:
                return Player(await resp.json())

    async def get_players(self, users):
        """ Get multiple players' data from the API. """
        url = f'{self.base_url}/players/discord'
        discord_ids = {"discordIds": [user.id for user in users]}

        async with self.session.post(url=url, headers=self.headers, json=discord_ids) as resp:
            resp.raise_for_status()

            if resp.status == 200:
                players = await resp.json()
                return [Player(player_data) for player_data in players]

    async def start_match(self, team_one, team_two):
        """ Get a match server from the API. """
        url = f'{self.base_url}/match/start'
        teams = {
            'team_one': {user.id: user.display_name for user in team_one},
            'team_two': {user.id: user.display_name for user in team_two}
        }

        async with self.session.post(url=url, headers=self.headers, json=teams) as resp:
            resp.raise_for_status()

            if resp.status == 200:
                return MatchServer(await resp.json())
