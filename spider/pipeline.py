import json
import os
import time
from pathlib import Path

import requests
from PIL import Image
from playwright.sync_api import sync_playwright

import config
from logger import logger


# json
def load_from_json(file: Path) -> dict | list:
    """Load JSON data, returning an empty dictionary when the file is absent."""
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"fail to load {file}")
        return {}
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"fail to load {file} for {repr(e)}")
        raise RuntimeError(f"fail to load {file}") from e


def save_to_json(file: Path, content: dict | list) -> None:
    """Save JSON data atomically to avoid leaving a partial output file."""
    file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = file.with_suffix(file.suffix + ".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, file)
    finally:
        if temp_file.exists():
            temp_file.unlink()


# scv
def save_to_scv(file: Path, content: dict | list) -> None:
    """Reserved CSV output entry; CSV export is not used by the crawler."""
    pass


# image
def get_image_session() -> requests.Session:
    """Create an HTTP session containing the saved QQ Music cookies."""
    session = requests.Session()
    cookies = load_from_json(config.COOKIES_PATH)
    for cookie in cookies:
        session.cookies.set(
            cookie["name"],
            cookie["value"],
            domain=cookie.get("domain"),
            path=cookie.get("path", "/"),
        )
    return session


def download_image(
    url: str, file: Path, session: requests.Session
) -> None:
    """Download and validate an image, retrying temporary failures."""
    file.parent.mkdir(parents=True, exist_ok=True)
    if file.exists():
        try:
            with Image.open(file) as image:
                image.verify()
            return
        except (OSError, SyntaxError):
            logger.warning(f"remove invalid image {file}")
            file.unlink()
    # retry
    for retry in range(3):
        try:
            response = session.get(
                url, headers=config.HEADERS, timeout=config.TIMEOUT
            )
            if response.status_code == 429 or response.status_code >= 500:
                raise RuntimeError(f"temporary status_code: {response.status_code}")
            if response.status_code != 200:
                raise ValueError(f"status_code: {response.status_code}")
            if len(response.content) == 0:
                raise RuntimeError("content empty")
            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith('image/'):
                raise RuntimeError(f"content type: {content_type}")
            break
        except ValueError as e:
            logger.error(f"stop retrying {url} for {repr(e)}")
            raise
        except (requests.RequestException, RuntimeError) as e:
            logger.warning(f"fail to get response from {url} for {repr(e)}")
            time.sleep(config.SLEEP_TIME * 2**retry)
    else:
        logger.error(f"failed to open image_url {url}")
        raise RuntimeError(f"failed to open image_url {url}")
    temp_file = file.with_suffix(file.suffix + ".tmp")
    try:
        with open(temp_file, "wb") as f:
            f.write(response.content)
        with Image.open(temp_file) as image:
            image.verify()
        os.replace(temp_file, file)
    finally:
        if temp_file.exists():
            temp_file.unlink()
