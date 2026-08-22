import re
from PIL import Image
from datetime import datetime
from django.utils import timezone
from django.core.management.base import BaseCommand
from music_app.models import Singer, Song, Comment
from music_app.management.commands import config, pipeline
from music_app.management.commands.logger import logger

class Command(BaseCommand):
    help = "Import music data from JSON files"

    def handle(self, *args, **options):
        # import singer_data
        singer_path = config.RAW_DATA_PATH / "singer_list.json"
        singer_list = pipeline.load_from_json(singer_path)
        logger.info("got singer_list data")
        for data in singer_list.values():
            # id
            try:
                id = pipeline.get_id_from_url(data["url"], "singer")
            except:
                continue
            # add singer to sql
            Singer.objects.update_or_create(
                id = id,
                defaults={
                    "name": data["name"],
                    "url": data["url"],
                    "image_url": data["image_url"],
                    "info": data["info"],
                }
            )
            logger.info(f"added singer {data['name']}")

        # import song_data
        song_path = config.RAW_DATA_PATH / "song_list.json"
        song_list = pipeline.load_from_json(song_path)
        logger.info("got singer_list data")
        for data in song_list.values():
            # id
            try:
                id = pipeline.get_id_from_url(data["url"], "songDetail")
            except:
                continue
            # add song to sql
            song, created = Song.objects.update_or_create(
                id = id,
                defaults={
                    "name": data["song_name"],
                    "url": data["url"],
                    "image_url": data["image_url"],
                    "lyrics": data["lyrics"],
                }
            )
            logger.info(f"added song {data['song_name']}")
            # singers
            for singer_data in data["singer"]:
                try:
                    singer_id = pipeline.get_id_from_url(singer_data["url"], "singer")
                except:
                    continue
                try:
                    singer = Singer.objects.get(id=singer_id)
                except:
                    logger.warning(f"fail to find singer {singer_data['url']}")
                song.singers.add(singer)
                logger.info(f"built relationship between {data['song_name']} and {singer_data['name']}")
            # comments
            for i, comment_data in enumerate(data["comments"]):
                # time
                time_data = comment_data["time"]
                time = datetime(
                    year = int(time_data["year"]) if time_data["year"] is not None else datetime.now().year,
                    month = int(time_data["month"]),
                    day = int(time_data["day"]),
                    hour = int(time_data["hour"]),
                    minute = int(time_data["minute"]), 
                )
                # add comment to sql
                Comment.objects.update_or_create(
                    id = id + f"_{i+1}",
                    defaults={
                        "song": song,
                        "text": comment_data["text"],
                        "time": timezone.make_aware(time),
                    }
                )
                logger.info(f"add comment {comment_data['text'][:5]}... of song {data['song_name']}")