# api.py


class Player:
    """ Represents a player with the contents returned by the API. """

    def __init__(self, json):
        """ Set attributes. """
        self.steam = json['steam']
        self.discord = json['discord']
        self.discord_name = json['discord_name']
        self.id = json['id']
        self.score = json['score']
        self.kills = json['kills']
        self.deaths = json['deaths']
        self.assists = json['assists']
        self.suicides = json['suicides']
        self.tk = json['tk']
        self.shots = json['shots']
        self.hits = json['hits']
        self.headshots = json['headshots']
        self.connected = json['connected']
        self.rounds_tr = json['rounds_tr']
        self.rounds_ct = json['rounds_ct']
        self.lastconnect = json['lastconnect']
        self.knife = json['knife']
        self.glock = json['glock']
        self.hkp2000 = json['hkp2000']
        self.usp_silencer = json['usp_silencer']
        self.p250 = json['p250']
        self.deagle = json['deagle']
        self.elite = json['elite']
        self.fiveseven = json['fiveseven']
        self.tec9 = json['tec9']
        self.cz75a = json['cz75a']
        self.revolver = json['revolver']
        self.nova = json['nova']
        self.xm1014 = json['xm1014']
        self.mag7 = json['mag7']
        self.sawedoff = json['sawedoff']
        self.bizon = json['bizon']
        self.mac10 = json['mac10']
        self.mp9 = json['mp9']
        self.mp7 = json['mp7']
        self.ump45 = json['ump45']
        self.p90 = json['p90']
        self.galilar = json['galilar']
        self.ak47 = json['ak47']
        self.scar20 = json['scar20']
        self.famas = json['famas']
        self.m4a1 = json['m4a1']
        self.m4a1_silencer = json['m4a1_silencer']
        self.aug = json['aug']
        self.ssg08 = json['ssg08']
        self.sg556 = json['sg556']
        self.awp = json['awp']
        self.g3sg1 = json['g3sg1']
        self.m249 = json['m249']
        self.negev = json['negev']
        self.hegrenade = json['hegrenade']
        self.flashbang = json['flashbang']
        self.smokegrenade = json['smokegrenade']
        self.inferno = json['inferno']
        self.decoy = json['decoy']
        self.taser = json['taser']
        self.mp5sd = json['mp5sd']
        self.breachcharge = json['breachcharge']
        self.head = json['head']
        self.chest = json['chest']
        self.stomach = json['stomach']
        self.left_arm = json['left_arm']
        self.right_arm = json['right_arm']
        self.left_leg = json['left_leg']
        self.right_leg = json['right_leg']
        self.c4_planted = json['c4_planted']
        self.c4_exploded = json['c4_exploded']
        self.c4_defused = json['c4_defused']
        self.ct_win = json['ct_win']
        self.tr_win = json['tr_win']
        self.hostages_rescued = json['hostages_rescued']
        self.vip_killed = json['vip_killed']
        self.vip_escaped = json['vip_escaped']
        self.vip_played = json['vip_played']
        self.mvp = json['mvp']
        self.damage = json['damage']
        self.match_win = json['match_win']
        self.match_draw = json['match_draw']
        self.match_lose = json['match_lose']
        self.first_blood = json['first_blood']
        self.no_scope = json['no_scope']
        self.no_scope_dis = json['no_scope_dis']
        self.in_match = json['inMatch']


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
            if resp.status == 200:
                resp_json = await resp.json()

                if resp_json.get('discord') and resp_json.get('code'):
                    return f'{self.base_url}/discord/{resp_json["discord"]}/{resp_json["code"]}'

    async def is_linked(self, user):
        """ Check if a user has their account linked with the API. """
        url = f'{self.base_url}/discord/check/{user.id}'

        async with self.session.get(url=url, headers=self.headers) as resp:
            if resp.status == 200:
                resp_json = await resp.json()

                if resp_json.get('linked'):
                    return resp_json['linked']

    async def update_discord_name(self, user):
        """ Update a users API name to their current Discord display name. """
        url = f'{self.base_url}/discord/update/{user.id}'
        data = {'discord_name': user.display_name}

        async with self.session.post(url=url, headers=self.headers, data=data) as resp:
            return resp.status == 200

    async def get_player(self, user):
        """ Get player data from the API. """
        url = f'{self.base_url}/player/discord/{user.id}'

        async with self.session.get(url=url, headers=self.headers) as resp:
            if resp.status == 200:
                return Player(await resp.json())

    async def get_players(self, users):
        """ Get multiple players' data from the API. """
        url = f'{self.base_url}/players/discord'
        discord_ids = {"discordIds": [user.id for user in users]}

        async with self.session.post(url=url, headers=self.headers, json=discord_ids) as resp:
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
            if resp.status == 200:
                return MatchServer(await resp.json())
