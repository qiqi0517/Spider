import json
import re
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from music_app.management.commands.import_data_utils import config
from music_app.management.commands.import_data_utils.logger import logger
from music_app.models import Comment, Singer, Song


class Command(BaseCommand):
    help = "Import music data from JSON files"

    def handle(self, *args, **options):
        logger.info("data import started")
        try:
            with transaction.atomic():
                import_singer_data()
                import_song_data()
        except Exception:
            logger.exception("data import failed; database changes were rolled back")
            raise
        logger.info("data import completed")
        self.stdout.write(self.style.SUCCESS("Data import completed"))


def import_singer_data():
    """hidden, called by command.handle"""
    singer_path = config.RAW_DATA_PATH / "singer_list.json"
    singer_list = load_from_json(singer_path)
    logger.info("got singer_list data")
    for data in singer_list.values():
        # id
        singer_id = get_id_from_url(data["url"], "singer")
        if singer_id is None:
            continue
        # add singer to sql
        _, created = Singer.objects.update_or_create(
            id=singer_id,
            defaults={
                "name": data["name"],
                "url": data["url"],
                "image": f"singer/{singer_id}.jpg",
                "image_url": data["image_url"],
                "info": data["info"][3:],
                "info_text": "".join(data["info"][3:])
            }
        )
        action = "created" if created else "updated"
        logger.info(f"{action} singer {data['name']}")


def import_song_data():
    """hidden, called by command.handle"""
    song_path = config.RAW_DATA_PATH / "song_list.json"
    song_list = load_from_json(song_path)
    logger.info("got song_list data")
    for data in song_list.values():
        # id
        song_id = get_id_from_url(data["url"], "songDetail")
        if song_id is None:
            continue
        # add song to sql
        song, created = Song.objects.update_or_create(
            id=song_id,
            defaults={
                "name": data["song_name"],
                "url": data["url"],
                "image_url": data["image_url"],
                "image": f"song/{song_id}.jpg",
                "lyrics": data["lyrics"],
                "lyrics_text": "".join(data["lyrics"])
            }
        )
        action = "created" if created else "updated"
        logger.info(f"{action} song {data['song_name']}")
        # singers
        for singer_data in data["singer"]:
            singer_id = get_id_from_url(singer_data["url"], "singer")
            if singer_id is None:
                continue
            try:
                singer = Singer.objects.get(id=singer_id)
            except Singer.DoesNotExist:
                logger.warning(f"fail to find singer {singer_data['url']}")
                continue
            song.singers.add(singer)
            logger.info(f"built relationship between {data['song_name']} and {singer_data['name']}")
        # comments
        for comment_data in data["comments"]:
            text = comment_data.get("text")
            if not isinstance(text, str) or not text.strip():
                logger.warning(f"skipped blank comment of song {data['song_name']}")
                continue
            # time
            try:
                time_data = comment_data["time"]
                time = datetime(
                    year = int(time_data["year"]),
                    month = int(time_data["month"]),
                    day = int(time_data["day"]),
                    hour = int(time_data["hour"]),
                    minute = int(time_data["minute"]),
                )
                time = timezone.make_aware(time)
            except (KeyError, TypeError, ValueError) as e:
                logger.warning(f"fail to parse comment time for {data['song_name']}: {e}")
                continue
            # add comment to sql
            comments = Comment.objects.filter(song=song, text=text, time=time).order_by("id")
            comment = comments.first()
            if comment is None:
                Comment.objects.create(song=song, text=text, time=time)
                logger.info(f"created comment of song {data['song_name']}")
            else:
                removed, _ = comments.exclude(pk=comment.pk).delete()
                logger.info(f"comment of song {data['song_name']} already exists")
                if removed:
                    logger.warning(f"removed {removed} duplicate comments of song {data['song_name']}")


# utils
def load_from_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"fail to load {file}: {e}")
        raise RuntimeError(f"fail to load {file}") from e


def get_id_from_url(url: str, resource_type: str):
    match = re.fullmatch(
        rf"https://y\.qq\.com/n/ryqq_v2/{re.escape(resource_type)}/(\w+)", url
    )
    if match is None:
        logger.warning(f"fail to find {resource_type}_id from {url}")
        return None
    return match.group(1)
