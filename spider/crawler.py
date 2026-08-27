import os
import random
import re
import time

import requests
from playwright.sync_api import (
    BrowserContext,
    Error as PlaywrightError,
    Page,
    sync_playwright,
)

import config
import parser
import pipeline
from logger import logger


# get_page functions
def get_music_data() -> None:
    """Collect and parse singer and song pages."""
    for retry in range(5):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context(storage_state=config.QQ_STATE_PATH)
                page = open_page(context, config.BASIC_URL + "/n/ryqq_v2/singer_list")
                singer_items = page.locator(
                    'ul.singer_list_txt li.singer_list_txt__item a'
                )
                singer_count = singer_items.count()
                no_growth_count = 0
                for _ in range(100):
                    if singer_count >= 300:
                        break
                    page.evaluate("window.scrollBy(0, window.innerHeight)")
                    page.wait_for_timeout(config.SLEEP_TIME * 1e3)
                    new_count = singer_items.count()
                    if new_count == singer_count:
                        no_growth_count += 1
                        if no_growth_count >= 5:
                            raise RuntimeError("singer list stopped loading")
                    else:
                        no_growth_count = 0
                    singer_count = new_count
                else:
                    raise RuntimeError("singer list did not reach 300 items")
                parser.parse_music_data(page, context)
                browser.close()
                logger.info("succeed with getting music data!")
                break
        except Exception as e:
            logger.error(f"browser enconter error: {str(e)}")
            if retry == 4:
                logger.fatal("frequent interruption, program ends")
                raise RuntimeError("frequent interruption, program ends") from e
            wait_time = min(config.SLEEP_TIME * 2**retry * 30, 120)
            logger.warning(f"retrying after {wait_time} seconds")
            time.sleep(wait_time)



def get_singer_page(
    url: str, context: BrowserContext, get_songs: bool = True
) -> tuple[dict, dict]:
    """Load and parse one singer page."""
    singer_data = {"url": url}
    page = open_page(context, url)
    page.locator("div.main").wait_for(timeout=config.TIMEOUT * 1e3)
    page.wait_for_timeout(random.uniform(1, config.SLEEP_TIME) * 1e3)
    try:
        detailed_singer_data, songs = parser.parse_singer_page(
            page, context, parse_songs=get_songs
        )
    except Exception as e:
        page.close()
        logger.error(f"fail to parse singer_page {url} for {str(e)}")
        raise RuntimeError(f"fail to parse singer_page {url} for {str(e)}")
    page.close()
    singer_data.update(detailed_singer_data)
    return singer_data, songs


def get_song_page(url: str, context: BrowserContext) -> dict:
    """Load and parse one song page."""
    song_data = {
        "url": url
    }
    page = open_page(context, url)
    # wait for lyrics to appear
    page.wait_for_function(
        """() => {
            const el = document.querySelector('#lrc_content');
            return el && el.innerText.trim() !== '';
        }""",
        timeout=config.TIMEOUT * 1e3
    )
    page.wait_for_timeout(random.uniform(1, config.SLEEP_TIME) * 1e3)
    try:
        detailed_song_data = parser.parse_song_page(page)
    except Exception as e:
        page.close()
        logger.error(f"fail to parse song_page {url} for {str(e)}")
        raise RuntimeError(f"fail to parse song_page {url} for {str(e)}")
    page.close()
    song_data.update(detailed_song_data)
    return song_data


def get_singer_from_song(
    song_info: dict, singer_list: dict, context: BrowserContext
) -> None:
    """Add singers discovered on a song page to the singer list."""
    song_url = song_info["url"]
    for song_singer in song_info["singer"]:
        singer_url = song_singer["url"]
        if singer_url not in singer_list:
            try:
                singer_info, _ = get_singer_page(singer_url, context, get_songs=False)
            except RuntimeError as e:
                logger.warning(
                    f"fail to find singer{singer_url} of song{song_url} for {str(e)}"
                )
                continue
            singer_list[singer_url] = singer_info
            logger.info(f"added singer {singer_url} to list")
        if song_url not in singer_list[singer_url]["song_urls"]:
            singer_list[singer_url]["song_urls"].append(song_url)
            logger.info(f"added song {song_url} to singer {singer_url}")


def get_images() -> None:
    """Download singer and song images from collected metadata."""
    session = pipeline.get_image_session()
    singer_list = pipeline.load_from_json(config.RAW_PATH / "singer_list.json")
    for singer in singer_list.values(): # type: ignore
        try:
            filename = re.match(
                r"^https://y.qq.com/n/ryqq_v2/singer/(\w+)$", singer["url"]
            ).group(1)  # type: ignore
            pipeline.download_image(
                singer["image_url"],
                config.IMAGE_PATH / "singer" / f"{filename}.jpg",
                session,
            )
            logger.info(f"image {singer['image_url']} successfully saved")
        except Exception as e:
            logger.error(
                f"fail to download singer_image {singer['image_url']} for {repr(e)}"
            )
        time.sleep(random.uniform(1, config.SLEEP_TIME))
    song_list = pipeline.load_from_json(config.RAW_PATH / "song_list.json")
    for song in song_list.values(): # type: ignore
        try:
            filename = re.match(
                r"^https://y.qq.com/n/ryqq_v2/songDetail/(\w+)$", song["url"]
            ).group(1)  # type: ignore
            pipeline.download_image(
                song["image_url"],
                config.IMAGE_PATH / "song" / f"{filename}.jpg",
                session,
            )
            logger.info(f"image {song['image_url']} successfully saved")
        except Exception as e:
            logger.error(
                f"fail to download song_image {song['image_url']} for {repr(e)}"
            )
        time.sleep(random.uniform(1, config.SLEEP_TIME))
    session.close()



# utils
def open_page(context: BrowserContext, url: str) -> Page:
    """Open a page and retry temporary Playwright failures."""
    page = context.new_page()
    for retry in range(3):
        try:
            page.goto(url, timeout=config.TIMEOUT * 1e3)
            return page
        except PlaywrightError as e:
            logger.warning(f"fail to load page {url} for {str(e)}")
            page.wait_for_timeout(config.SLEEP_TIME * 2**retry * 1e3)
    else:
        page.close()
        logger.error(f"failed to open page {url}")
        raise RuntimeError(f"failed to open page {url}")
