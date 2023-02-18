
import base64
import hashlib
from urllib.parse import quote
from functools import lru_cache
from astra.api import config

def hash_b64safe(data: bytes):
    return base64.urlsafe_b64encode(hashlib.sha256(data).digest()).replace(b'=', b'').decode('utf-8')

@lru_cache(maxsize=None)
def get_bot_wh_path():
    token_hash = hash_b64safe(config.TOKEN.encode('utf-8'))
    return f"/bot/{quote(token_hash)}"

@lru_cache(maxsize=None)
def get_bot_wh_endpoint():
    return get_hostname() + get_bot_wh_path()

@lru_cache(maxsize=None)
def get_hostname():
    if config.TG_WH_HOSTNAME.lower() == 'ngrok':
        config.TG_WH_HOSTNAME = get_ngrok_hostname()
        if config.TG_WH_HOSTNAME is None:
            raise Exception("TG_WH_HOSTNAME setted to 'ngrok' but ngrok is not avaliable!")
        
    return config.TG_WH_HOSTNAME


def get_ngrok_hostname():
    import requests

    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=3)
        if not response.ok: return None
   
        return response.json()['tunnels'][0]['public_url']
    except KeyError or ConnectionError:
        return None
    