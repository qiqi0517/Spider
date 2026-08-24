import json
from playwright.sync_api import sync_playwright
from pathlib import Path
from logger import logger

LOCAL_CONFIG_DIR = Path(__file__).resolve().parent / "local_config"
COOKIES_PATH = LOCAL_CONFIG_DIR / "cookies.json"
QQ_STATE_PATH = LOCAL_CONFIG_DIR / "qq_state.json"
BASE_URL = "https://y.qq.com/"


def get_local_config():
    LOCAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto(BASE_URL, wait_until="domcontentloaded")
        print("Please log in qqMusic")
        input("Please press Enter after logging in")
        # cookies.json
        cookies = context.cookies()
        with open(LOCAL_CONFIG_DIR / "cookies.json", "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=4)
        # qq_state.json
        context.storage_state(path = LOCAL_CONFIG_DIR / "qq_state.json")
        logger.info("succeed in getting local config")
        browser.close()


if __name__ == "__main__":
    get_local_config()