import config_local

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
BASIC_URL = "https://y.qq.com"
HEADERS = {
    "Cookie": config_local.COOKIE_STR,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    "Referer": "https://www.google.com/"
}

TIMEOUT = 10
SLEEP_TIME = 2
NO_INFO = '-'

# Address
SINGER_LIST_HTML_ADDRESS = "../data/html/singer_list.html"
SINGERS_HTML_ADDRESS = "../data/html/singers"
SONGS_HTML_ADDRESS = "../data/html/songs"
RAW_PATH = "../data/raw"
IMAGE_PATH = "../data/image"