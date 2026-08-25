import json, time
from django.conf import settings
from music_app.models import Singer, Song
from music_app import config

INDEX_PATH = settings.BASE_DIR / "data"

# search via index_map
def search_songs(query: str):
    start_time = time.time()
    candidate_ids = get_candidate(config.SONG_INDEX, query)
    # verify cadidate   
    if len(query) <= 2:
        search_result = Song.objects.filter(id__in = candidate_ids)
    else:
        candidate_songs = Song.objects.filter(id__in = candidate_ids).prefetch_related("singers")
        search_result = []
        for song in candidate_songs:
            # name
            if query in song.name:
                search_result.append(song)
                continue
            # singers
            for singer in song.singers.all():
                if query in singer.name:
                    search_result.append(song)
                    continue
            # lyrics
            if query in "".join(song.lyrics):
                search_result.append(song)
    end_time = time.time()
    return search_result, end_time - start_time


def search_singers(query: str):
    start_time = time.time()
    candidate_ids = get_candidate(config.SINGER_INDEX, query)
    # verify cadidate
    if len(query) <= 2:
        search_result = Singer.objects.filter(id__in = candidate_ids)
    else:
        candidate_singers = Singer.objects.filter(id__in = candidate_ids)
        search_result = []
        for singer in candidate_singers:
            # name
            if query in singer.name:
                search_result.append(singer)
                continue
            # lyrics
            if query in "".join(singer.info):
                search_result.append(singer)
    end_time = time.time()
    return search_result, end_time - start_time




# utils
def get_candidate(index_map: dict[str, list[str]], query: str):
    if len(query) <= 2:
        return set(index_map.get(query, []))
    gram_candidates = []
    for i in range(len(query)-1):
        gram = query[i:i+2]
        gram_candidates.append(set(index_map.get(gram, [])))
    return set.intersection(*gram_candidates)