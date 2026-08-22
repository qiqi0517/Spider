import json, re
from music_app.management.commands.logger import logger

def load_from_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        logger.error(f"fail to load {file}")
        raise RuntimeError(f"fail to load {file}")

def get_id_from_url(url, type: str):
    try:
        id = re.match(f"^https://y.qq.com/n/ryqq_v2/{type}/(\w+)$", url).group(1)   # type: ignore
    except Exception as e:
        logger.warning(f"fail to find {type}_id from {url} for {repr(e)}")
    return id