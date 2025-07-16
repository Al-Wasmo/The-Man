import os
from datetime import datetime
import re

env = {}
HEADERS = {}

def init():
    # Loads environment variables from a .env file into the global `env` dictionary and initializes HTTP `HEADERS` for LinkedIn requests.
    # Creates output directory if not created

    global env
    global HEADERS
    with open(".env","r") as f:
        for line in f:
            if not line:
                continue

            key = line.split(" ")[0]
            val = " ".join(line.split(" ")[1:]).strip()
            env[key] = val
    assert "cookie" in env and "cookie must be in the env"



    csrf_token = re.search(r"ajax:\d+",env["cookie"]).group()
    HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0',
    'Accept': 'application/vnd.linkedin.normalized+json+2.1',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'csrf-token': csrf_token,
    'Alt-Used': 'www.linkedin.com',
    'Connection': 'keep-alive',
    'Referer': 'https://www.linkedin.com/feed/',
    'Cookie':  env["cookie"],
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'TE': 'trailers',
    }




    os.makedirs("output/model",exist_ok=True)
    os.makedirs("output/actions",exist_ok=True)


def nested_get(d, keys, default=None):
    # Safely retrieves a nested value from a dictionary using a list of keys; returns `default` if any key is missing or type mismatch occurs.

    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, default)
        else:
            return default
    return d



def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d:%H:%M:%S")