import os
from datetime import datetime

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

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0',
        'Accept': 'application/vnd.linkedin.normalized+json+2.1',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'x-li-lang': 'en_US',
        'x-li-track': '{"clientVersion":"1.13.37080","mpVersion":"1.13.37080","osName":"web","timezoneOffset":1,"timezone":"Africa/Algiers","deviceFormFactor":"DESKTOP","mpName":"voyager-web","displayDensity":1.0909090909090908,"displayWidth":1919.9999999999998,"displayHeight":1080}',
        'x-li-page-instance': 'urn:li:page:d_flagship3_profile_view_create_post;xRLRrkjVTSq8FZtUjRBGfQ==',
        'csrf-token': 'ajax:6740192219103647140',
        'x-restli-protocol-version': '2.0.0',
        'x-li-pem-metadata': 'Voyager - Sharing - CreateShare=sharing-create-content',
        'content-type': 'application/json; charset=utf-8',
        'Origin': 'https://www.linkedin.com',
        'Referer': 'https://www.linkedin.com/in/mahdi-benhom-93a235375/overlay/create-post/',
        'Cookie': env["cookie"], 
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