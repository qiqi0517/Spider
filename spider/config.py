from pathlib import Path

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
)
BASIC_URL = "https://y.qq.com"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Referer": BASIC_URL + "/",
}

TIMEOUT = 10
SLEEP_TIME = 2
NO_INFO = "-"

# Address
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
LOCAL_CONFIG_DIR = BASE_DIR / "local_config"
COOKIES_PATH = LOCAL_CONFIG_DIR / "cookies.json"
QQ_STATE_PATH = LOCAL_CONFIG_DIR / "qq_state.json"
SINGER_LIST_HTML_ADDRESS = DATA_DIR / "html" / "singer_list.html"
SINGERS_HTML_ADDRESS = DATA_DIR / "html" / "singers"
SONGS_HTML_ADDRESS = DATA_DIR / "html" / "songs"
RAW_PATH = DATA_DIR / "raw"
IMAGE_PATH = DATA_DIR / "image"
LOG_PATH = PROJECT_DIR / "logs"
