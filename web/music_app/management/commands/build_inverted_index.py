import json
from django.core.management.base import BaseCommand
from music_app.models import Singer, Song
from music_app.management.commands.build_inverted_index_utils import config
from music_app.management.commands.build_inverted_index_utils.logger import logger

class Command(BaseCommand):
    help = "Import music data from JSON files"

    def handle(self, *args, **options):
        build_song_index()
        build_singer_index()



# build inverted index
def build_song_index():
    song_index = {}
    for song in Song.objects.all():
        logger.info(f"building index of {song.name}")
        # song_name
        add_to_index(song_index, song.name, song.id)
        # singer_names
        for singer in song.singers.all():
            add_to_index(song_index, singer.name, song.id)
        # 歌词
        add_to_index(song_index, "".join(song.lyrics), song.id)
    save_index(song_index, config.INDEX_PATH / "song_index.json")
    logger.info("succeed in building song_index")


def build_singer_index():
    singer_index = {}
    for singer in Singer.objects.all():
        logger.info(f"building index of {singer.name}")
        # singer_name
        add_to_index(singer_index, singer.name, singer.id)
        # info
        add_to_index(singer_index, "".join(singer.info), singer.id)
    save_index(singer_index, config.INDEX_PATH / "singer_index.json")
    logger.info("succeed in building singer_index")



# utils
def add_to_index(index_map: dict[str, set], text: str, id: str):
    unigram = generate_ngrams(text, 1)
    bigram = generate_ngrams(text, 2)
    for gram in unigram + bigram:
        if len(gram.strip()) == 0:
            continue
        if gram in index_map:
            index_map[gram].add(id)
        else:
            index_map[gram] = {id}


def generate_ngrams(text: str, n):
    if len(text) < n:
        return []
    return [text[i:i+n] for i in range(len(text)-n+1)]     


def save_index(index_map: dict[str, set], file_path):
    index_to_save = {}
    for gram, index_set in index_map.items():
        index_to_save[gram] = list(index_set)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(index_to_save, f, ensure_ascii=False, indent=4)
