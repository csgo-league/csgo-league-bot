# link process
# !login - https://github.com/csgo-league/csgo-league-bot/blob/develop/src/commands/login.js#L13
# Send a GET request to /discord/generate/{DISCORD_ID} which returns the 'code' in the body of the json response
# If code is not a falsy value send a message to the channel telling the user to check their PMs
# send PM containing link to /discord/{DISCORD_ID}/{CODE}

# check process
# !check - https://github.com/csgo-league/csgo-league-bot/blob/develop/src/commands/check.js#L13
# send POST request to /discord/update/{DISCORD_ID} with a body of {discord_name: '{DISCORD_NAME}'}
# if error = link_discord start link process

# As people join the queue check they're linked with the system
# If not linked -> follow link process
# Else add to queue

# loop through queue and get players steam ID and rank score from the backend via
# GET request to /player/discord/{DISCORD_ID}

# Get available IP and Ports of the servers via GET request to /servers

# format the player data from the endpoint and then send it off to
# POST /match/start
# Example:
# {
#     "ip": "",
#     "port": "",
#     "team_one": {
#             "{STEAM64 ID}": "{Discord Name}"
#     },
#     "team_two": {
#             "7651234678123": "Shane"
#     }
# }

# api.py

import requests

def get_code(base_url, api_key, discord_id):
    url = f'{base_url}/discord/generate/{discord_id}'
    return requests.get(url=url, headers={'authentication': api_key})

def post_check(base_url, api_key, discord_id, discord_name):
    url = f'{base_url}/discord/update/{discord_id}'
    return requests.post(url=url, headers={'authentication': api_key}, data={'discord_name': discord_name})

def get_discord(base_url, api_key, discord_id):
    url = f'{base_url}/player/discord/{discord_id}'
    return requests.get(url=url, headers={'authentication': api_key})

def request_server(base_url, api_key, team_one, team_two):
    url = f'{base_url}/match/start'
    data = {}
    data['team_one'] = team_one
    data['team_two'] = team_two
    return requests.post(url=url, headers={'authentication': api_key}, json=data)

# Can't run as main right now because of module comflicts
# API_KEY = 'XXXXXXXX'
# r = request_server('http://pugs.viquity.pro', API_KEY, {"76561198054402080": "Shane"}, {"76561198028510846": "B3none"})
# print(r)
# print(r.json())
