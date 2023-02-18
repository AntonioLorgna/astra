
import base64
import hashlib
import os
from urllib.parse import quote
from functools import lru_cache

def hash_b64safe(data: bytes):
    return base64.urlsafe_b64encode(hashlib.sha256(data).digest()).replace(b'=', b'').decode('utf-8')

@lru_cache(maxsize=None)
def get_wh_path():
    TOKEN = os.environ.get("TG_TOKEN")
    if TOKEN is None:
        raise Exception("TG_TOKEN is empty!")
    token_hash = hash_b64safe(TOKEN.encode('utf-8'))
    return f"/bot/{quote(token_hash)}"

@lru_cache(maxsize=None)
def get_wh_endpoint():
    return get_hostname() + get_wh_path()

@lru_cache(maxsize=None)
def get_hostname():
    HOSTNAME = os.environ.get("HOSTNAME")
    if HOSTNAME is None:
        HOSTNAME = get_ngrok_hostname()
        
    if HOSTNAME is None:
        raise Exception("HOSTNAME is empty!")
    
    return HOSTNAME


def get_ngrok_hostname():
    import requests


    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=3)
        if not response.ok: return None
   
        return response.json()['tunnels'][0]['public_url']
    except KeyError or ConnectionError:
        return None