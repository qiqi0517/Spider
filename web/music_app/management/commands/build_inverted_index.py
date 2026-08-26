import json, math, os
from collections import defaultdict
from django.core.management.base import BaseCommand
from music_app.models import Singer, Song
from music_app.management.commands.build_inverted_index_utils import config
from music_app.management.commands.build_inverted_index_utils.logger import logger

class Command(BaseCommand):
    help = "Import music data from JSON files"

    def handle(self, *args, **options):
        logger.info("start building inverted indexes")
        try:
            build_song_index()
            build_singer_index()
        except Exception:
            logger.exception("fail to build inverted indexes")
            raise
        logger.info("finished building inverted indexes; restart runserver to reload them")



# build inverted index
def build_song_index():
    song_index = defaultdict(dict)
    # add items
    songs = Song.objects.prefetch_related("singers")
    for song in songs:
        logger.info(f"building index of {song.name}")
        # song_name
        add_to_index(song_index, song.name, song.id)
        # singer_names
        for singer in song.singers.all():
            add_to_index(song_index, singer.name, song.id)
        # lyrics
        add_to_index(song_index, song.lyrics_text, song.id)
    # calculate tfidf
    logger.info("calculating song tf-idf")
    num_songs = Song.objects.count()
    for map_id_tf in song_index.values():
        df = len(map_id_tf)
        idf = math.log((num_songs+1)/(df+1))+1
        for id, tf in map_id_tf.items():
            map_id_tf[id] = round(tf * idf, 6)
    save_indexes(song_index, "song")
    logger.info("succeed in building song_index")


def build_singer_index():
    singer_index = defaultdict(dict)
    # add items
    for singer in Singer.objects.all():
        logger.info(f"building index of {singer.name}")
        # singer_name
        add_to_index(singer_index, singer.name, singer.id)
        # info
        add_to_index(singer_index, singer.info_text, singer.id)
    # calculate tfidf
    logger.info("calculating singer tf-idf")
    num_singers = Singer.objects.count()
    for map_id_tf in singer_index.values():
        df = len(map_id_tf)
        idf = math.log((num_singers+1)/(df+1))+1
        for id, tf in map_id_tf.items():
            map_id_tf[id] = round(tf * idf, 6)
    save_indexes(singer_index, "singer")
    logger.info("succeed in building singer_index")



# utils
def add_to_index(index_map: defaultdict[str, dict], text: str, id: str):
    unigram = generate_ngrams(text, 1)
    bigram = generate_ngrams(text, 2)
    for gram in unigram + bigram:
        if len(gram.strip()) == 0:
            continue
        index_map[gram][id] = index_map[gram].get(id, 0) + 1


def generate_ngrams(text: str, n):
    if len(text) < n:
        return []
    return [text[i:i+n] for i in range(len(text)-n+1)]


def save_indexes(index_map, index_name):
    unigram_index = {gram: value for gram, value in index_map.items() if len(gram) == 1}
    bigram_index = {gram: value for gram, value in index_map.items() if len(gram) == 2}
    save_index(unigram_index, config.INDEX_PATH / f"{index_name}_unigram_index.json")
    save_index(bigram_index, config.INDEX_PATH / f"{index_name}_bigram_index.json")


def save_index(index_map, file_path):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = file_path.with_suffix(file_path.suffix + ".tmp")
    logger.info(f"saving index to {file_path}")
    try:
        with open(temporary_path, "w", encoding="utf-8") as f:
            json.dump(index_map, f, ensure_ascii=False, separators=(",", ":"))
        os.replace(temporary_path, file_path)
    finally:
        temporary_path.unlink(missing_ok=True)
