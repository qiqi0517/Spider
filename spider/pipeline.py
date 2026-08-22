import json, requests, time, os
from playwright.sync_api import sync_playwright
from logger import logger
import config

# json
def load_from_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        logger.warning(f"fail to load {file}")
        return {}
    
def save_to_json(file, content):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=4)


# scv
def save_to_scv(file, content):
    pass


# image
def download_image(url, file):
    if os.path.exists(file):
        return
    cookies = load_from_json("cookies.json")
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(
            cookie["name"],
            cookie["value"],
            domain=cookie.get("domain"),
            path=cookie.get("path", "/")
        )
    # retry
    for retry in range(3):
        try:
            response = session.get(url, headers=config.HEADERS, timeout=config.TIMEOUT)
            if response.status_code != 200:
                raise ValueError(f"status_code: {response.status_code}")
            if len(response.content) == 0:
                raise ValueError(f"content empty")
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                raise ValueError(f"content type: {content_type}")
            break
        except Exception as e:
            logger.warning(f"fail to get response from {url} for {repr(e)}")
            time.sleep(config.SLEEP_TIME * 2**retry)
    else:
        logger.error(f"failed to open image_url {url}")
        raise RuntimeError(f"failed to open image_url {url}")
    with open(file, "wb") as f:
        f.write(response.content)
    