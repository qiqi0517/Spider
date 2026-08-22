import requests, os, time, re
from PIL import Image
from playwright.sync_api import sync_playwright, BrowserContext
import config, parser, pipeline
from logger import logger

# get_page functions
def get_music_data():
    """public"""
    for retry in range(5):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context(storage_state="qq_state.json")
                page = open_page(context, config.BASIC_URL+"/n/ryqq_v2/singer_list")
                # roll to bottom twice
                while page.locator('ul.singer_list_txt li.singer_list_txt__item a').count() < 300:
                    page.evaluate(
                        "window.scrollBy(0, window.innerHeight)"
                    )
                    page.wait_for_timeout(config.SLEEP_TIME*1e3)
                parser.parse_music_data(page, context)
                browser.close()
                logger.info("succeed with getting music data!")
                break
        except Exception as e:
            logger.error(f"browser enconter error: {str(e)}")
            time.sleep(config.SLEEP_TIME * 2**retry * 1e3 * 30)
    else:
        logger.fatal("frequent interruption, program ends")



def get_singer_page(url, context: BrowserContext, get_songs=True) -> tuple[dict, dict]:
    """hidden, called by parse_music_data()"""
    singer_data = {"url": url}
    page = open_page(context, url)
    page.wait_for_timeout(config.TIMEOUT*1e3)
    try:
        detailed_singer_data, songs = parser.parse_singer_page(page, context, parse_songs=get_songs)
    except Exception as e:
        page.close()
        logger.error(f"fail to parse singer_page {url} for {str(e)}")
        raise RuntimeError(f"fail to parse singer_page {url} for {str(e)}")
    page.close()
    singer_data.update(detailed_singer_data)
    return singer_data, songs


def get_song_page(url, context: BrowserContext) -> dict: 
    """hidden, called by parse_singer_page()"""
    song_data = {
        "url": url
    }
    page = open_page(context, url)
    # wait for lyrics to appear
    page.wait_for_function(
        """() => {
            const el = document.querySelector('#lrc_content');
            return el && el.innerText.trim() !== '暂无歌词';
        }"""
    )
    page.wait_for_timeout(config.SLEEP_TIME*1e3)
    try:
        detailed_song_data = parser.parse_song_page(page)
    except Exception as e:
        page.close()
        logger.error(f"fail to parse song_page {url} for {str(e)}")
        raise RuntimeError(f"fail to parse song_page {url} for {str(e)}")
    page.close()
    song_data.update(detailed_song_data)
    return song_data


def get_singer_from_song(song_info, singer_list, context: BrowserContext):
    """hidden, called by parse_music_data"""
    song_url = song_info["url"]
    for song_singer in song_info["singer"]:
        singer_url = song_singer["url"]
        if singer_url not in singer_list:
            try:
                singer_info, _ = get_singer_page(singer_url, context, get_songs=False)
            except Exception as e:
                logger.warning(f"fail to find singer{singer_url} of song{song_url} for {str(e)}")
                continue
            singer_list[singer_url] = singer_info
            logger.info(f"added singer {singer_url} to list")
        if song_url not in singer_list[singer_url]["song_urls"]:
            singer_list[singer_url]["song_urls"].append(song_url)
            logger.info(f"added song {song_url} to singer {singer_url}")


def get_images():
    """public"""
    singer_list = pipeline.load_from_json(config.RAW_PATH + "/singer_list.json")
    for singer in singer_list.values():
        try:
            filename = re.match(r"^https://y.qq.com/n/ryqq_v2/singer/(\w+)$", singer["url"]).group(1)   # type: ignore
            pipeline.download_image(singer["image_url"], config.IMAGE_PATH + f"/singers/{filename}.jpg")
            with Image.open(config.IMAGE_PATH + f"/singers/{filename}.jpg") as img:
                img.verify()
            logger.info(f"image {singer['image_url']} successfully saved")
        except Exception as e:
            logger.error(f"fail to download singer_image {singer['image_url']} for {repr(e)}")
        time.sleep(config.SLEEP_TIME)
    song_list = pipeline.load_from_json(config.RAW_PATH + "/song_list.json")
    for song in song_list.values():
        try:
            filename = re.match(r"^https://y.qq.com/n/ryqq_v2/songDetail/(\w+)$", song["url"]).group(1) # type: ignore
            pipeline.download_image(song["image_url"], config.IMAGE_PATH + f"/songs/{filename}.jpg")
        except Exception as e:
            logger.error(f"fail to download song_image {song['image_url']} for {repr(e)}")
        time.sleep(config.SLEEP_TIME)



# utils
def open_page(context: BrowserContext, url):
    """hidden, called by get_page functions"""
    page = context.new_page()
    for retry in range(3):
        try:
            page.goto(url, timeout = config.TIMEOUT*1e3)
            return page
        except Exception as e:
            logger.warning(f"fail to load page {url} for {str(e)}")
            page.wait_for_timeout(config.SLEEP_TIME * 2**retry * 1e3)
    else:
        page.close()
        logger.error(f"failed to open page {url}")
        raise RuntimeError(f"failed to open page {url}")
