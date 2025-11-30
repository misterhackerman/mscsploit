import os
from fake_useragent import FakeUserAgent
ua = FakeUserAgent()

# this is home + your favorite dir
FOLDER = os.path.expanduser("~") + '/dox/med'
HEADERS  = {
            "User-Agent": 'curl/8.17.0',
            "Accept-Encoding": "identity"
        }
DECOR = ' \033[34;1m::\033[0m '
EXTENSIONS = ["pdf", "ppt", "doc"]
