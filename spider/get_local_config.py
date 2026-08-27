import json

from playwright.sync_api import sync_playwright

import config
from logger import logger

BASE_URL = "https://y.qq.com/"


def get_local_config() -> None:
    """Open QQ Music login and save cookies and browser state locally."""
    config.LOCAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        try:
            context = browser.new_context()
            page = context.new_page()
            page.goto(BASE_URL, wait_until="domcontentloaded")
            print("Please log in qqMusic")
            input("Please press Enter after logging in")
            # cookies.json
            cookies = context.cookies()
            with open(config.COOKIES_PATH, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=4)
            # qq_state.json
            context.storage_state(path=config.QQ_STATE_PATH)
            logger.info("succeed in getting local config")
        finally:
            browser.close()


if __name__ == "__main__":
    get_local_config()
