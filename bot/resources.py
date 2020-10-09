from aiohttp import ClientSession


class Sessions:
    requests: ClientSession


class Config:
    api_url: str
