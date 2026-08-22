import re, time
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, BrowserContext, Locator
import crawler, config, pipeline
from logger import logger

def parse_music_data(page: Page, context: BrowserContext):
    """hidden, called by get_music_data()"""
    singer_list = pipeline.load_from_json(config.RAW_PATH + "/singer_list.json")
    song_list = pipeline.load_from_json(config.RAW_PATH + "/song_list.json")
    current_num_singer = len(singer_list)
    # get data from singers
    sublist1 = page.locator('div.mod_singer_list li.singer_list__item h3.singer_list__title a')
    sublist2 = page.locator('ul.singer_list_txt li.singer_list_txt__item a')
    def parse_singer(singer: Locator, id):
        try:
            href = singer.get_attribute("href")
        except:
            logger.warning(f"fail to find singer's href")
            return
        url = config.BASIC_URL + str(href)
        try:
            singer_data, songs = crawler.get_singer_page(url, context)
        except:
            return
        singer_list[url] = singer_data
        song_list.update(songs)
        pipeline.save_to_json(config.RAW_PATH + "/singer_list.json", singer_list)
        pipeline.save_to_json(config.RAW_PATH + "/song_list.json", song_list)
        if id % 10 == 0:
            pipeline.save_to_json(config.RAW_PATH + f"/checkpoint/singer_list/singer_list_{id}.json", singer_list)
            pipeline.save_to_json(config.RAW_PATH + f"/checkpoint/song_list/song_list_{id}.json", song_list)
            logger.info(f"already get: singer_data {len(singer_list)}, song_data {len(song_list)}")
    num_singer_1, num_singer_2 = sublist1.count(), sublist2.count()
    for i in range(current_num_singer, num_singer_1): 
        parse_singer(sublist1.nth(i), i)
    for i in range(max(0, current_num_singer-num_singer_1), num_singer_2): 
        parse_singer(sublist2.nth(i), i + num_singer_1)
    # get data from songs
    for i, song in enumerate(song_list.values()):
        try:
            crawler.get_singer_from_song(song, singer_list, context)
        except Exception as e:
            logger.error(f"when geting singer from song: {repr(e)}")
            continue
        if i % 10 == 0:
            pipeline.save_to_json(config.RAW_PATH + "/singer_list.json", singer_list)
        if i % 100 == 0:
            pipeline.save_to_json(config.RAW_PATH + f"/checkpoint/singer_list/singer_list_extra_{i}.json", singer_list)
            logger.info(f"already check {i+1} songs")


def parse_singer_page(page: Page, context: BrowserContext, parse_songs=True) -> tuple[dict, dict]:
    """hidden, called by get_singer_page()"""
    # name
    name_locator = page.locator('div.data__name h1.data__name_txt')
    if name_locator.count() == 0:
        logger.warning(f"fail to find singer's name")
        name = config.NO_INFO
    else:
        name = name_locator.first.inner_text()
    logger.info(f"parsing {name}'s page")
    # image
    image_locator = page.locator('div.main img.data__photo')
    try:
        image_url = "https:" + str(image_locator.first.get_attribute("src", timeout=config.TIMEOUT*1e3))
    except:
        logger.warning(f"fail to find singer{name}'s image_url")
        image_url = config.NO_INFO        
    # info
    info = []
    info_locator = page.locator('div.popup_data_detail__cont p')
    for i in range(info_locator.count()):
        info.append(info_locator.nth(i).inner_text())
    # songs
    songs = {}
    song_urls = []
    if parse_songs == True:
        songs_locator = page.locator('ul.songlist__list li')
        num_songs = songs_locator.count()
        for song_id in range(num_songs):
            song = songs_locator.nth(song_id)
            song_url = config.BASIC_URL + str(song.locator('span.songlist__songname_txt a').get_attribute("href"))
            try:
                song_data = crawler.get_song_page(song_url, context)
            except:
                continue
            song_urls.append(song_url)
            songs[song_url] = song_data
    # construct & record singer_data
    detailed_singer_data = {
        "name": name,
        "image_url": image_url,
        "song_urls": song_urls,
        "info": info
    }
    return detailed_singer_data, songs

    

def parse_song_page(page: Page) -> dict:
    """hidden, called by get_song_page()"""
    # song_name
    song_name_locator = page.locator('div.data__name h1.data__name_txt')
    if song_name_locator.count() == 0:
        logger.warning("fail to find song name")
        song_name = config.NO_INFO
    else:
        song_name = song_name_locator.first.inner_text()
    # singer_name
    singer_locator = page.locator('div.data__singer a.data__singer_txt')
    num_singers = singer_locator.count()
    if num_singers == 0:
        logger.warning(f"fail to find singer")
        singer = config.NO_INFO
    else:
        singer = []
        for i in range(num_singers):
            ith_singer = singer_locator.nth(i)
            singer_name = ith_singer.inner_text()
            try:
                singer_href = ith_singer.get_attribute("href")
            except:
                singer_href = config.NO_INFO
                logger.warning(f"fail to find {song_name}'s singer{singer_name}'s href")
            singer.append({"name": singer_name, "url": config.BASIC_URL+singer_href})   # type: ignore
    # image
    image_locator = page.locator('div.main img.data__photo')
    try:
        image_url = "https:" + str(image_locator.first.get_attribute("src", timeout=config.TIMEOUT*1e3))
    except:
        logger.warning(f"fail to find song{song_name}'s image_url")
        image_url = config.NO_INFO
    # lyrics
    lyrics = []
    lyrics_locator = page.locator('div.lyric__cont_box p span')
    for i in range(lyrics_locator.count()):
        lyrics.append(lyrics_locator.nth(i).inner_text())
    # comments
    comments = []
    comments_locator = page.locator('div.mod_hot_comment > ul.comment__list > li > div:not(.comment__reply)')
    for i in range(min(comments_locator.count(), 5)):
        comment = comments_locator.nth(i)
        # comment.text
        text_locator = comment.locator('p.comment__text')
        if text_locator.count() == 0:
            logger.warning(f"fail to find text in {i}th comment of {song_name}")
            continue
        text = text_locator.first.inner_text()
        # comment.time
        time_locator = comment.locator('div.comment__date')
        if time_locator.count() == 0:
            logger.warning(f"fail to find time in {i}th comment of {song_name}")
            continue
        time_str = time_locator.inner_text()
        time_pattern = r'^(?:(\d{4})年)?(\d{1,2})月(\d{1,2})日 (\d{1,2}):(\d{2})'
        time_result = re.match(time_pattern, time_str)
        if not time_result:
            logger.warning(f"time_str {time_str} fail to match time format")
            continue
        year, month, day, hour, minute = time_result.groups()
        time = {
            "year": year,
            "month": month,  
            "day": day,    
            "hour": hour,   
            "minute": minute  
        }
        comments.append(
            {"text": text, "time": time}
        )

    # construct & record song_data
    detailed_song_data = {
        "song_name": song_name,
        "image_url": image_url,
        "singer": singer,
        "lyrics": lyrics,
        "comments": comments
    }
    return detailed_song_data