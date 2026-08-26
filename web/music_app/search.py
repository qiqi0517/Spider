import time
from functools import lru_cache
from django.db.models import Count, Prefetch
from music_app.models import Singer, Song
from music_app import config, rank, pipeline


@lru_cache(maxsize=2)
def get_song_index(gram_size):
    """Load and cache the song index needed by the query."""
    if gram_size == 1:
        return pipeline.load_index(config.SONG_UNIGRAM_INDEX_PATH)
    return pipeline.load_index(config.SONG_BIGRAM_INDEX_PATH)


@lru_cache(maxsize=2)
def get_singer_index(gram_size):
    """Load and cache the singer index needed by the query."""
    if gram_size == 1:
        return pipeline.load_index(config.SINGER_UNIGRAM_INDEX_PATH)
    return pipeline.load_index(config.SINGER_BIGRAM_INDEX_PATH)


# search via index_map
def search_songs(query: str):
    song_index = get_song_index(1 if len(query) == 1 else 2)
    candidate_id_tfidf = get_candidate(song_index, query)
    # verify cadidate and rank
    candidate_songs = Song.objects.filter(id__in = candidate_id_tfidf.keys()).only(
        "id", "name", "image", "image_url", "lyrics_text"
    ).prefetch_related(
        Prefetch("singers", queryset=Singer.objects.only("id", "name"))
    )
    search_result = []
    max_tfidf = 0
    for song in candidate_songs:
        tfidf = candidate_id_tfidf[song.id]
        rule_score = rank.calc_song_rule_score(song, query)
        if rule_score > 0:
            search_result.append((song, rule_score, tfidf))
            max_tfidf = max(tfidf, max_tfidf)
    ranked_result = [x[0] for x in sorted(search_result, key = lambda x: calc_score(x[1], x[2], max_tfidf, 5), reverse=True)]
    return ranked_result


def search_singers(query: str):
    singer_index = get_singer_index(1 if len(query) == 1 else 2)
    candidate_id_tfidf = get_candidate(singer_index, query)
    # verify cadidate and rank
    candidate_singers = Singer.objects.filter(id__in = candidate_id_tfidf.keys()).only(
        "id", "name", "image", "image_url", "info_text"
    ).annotate(song_count=Count("songs"))
    search_result = []
    max_tfidf = 0
    for singer in candidate_singers:
        tfidf = candidate_id_tfidf[singer.id]
        rule_score = rank.calc_singer_rule_score(singer, query)
        if rule_score > 0:
            search_result.append((singer, rule_score, tfidf))
            max_tfidf = max(tfidf, max_tfidf)
    ranked_result = [x[0] for x in sorted(search_result, key = lambda x: calc_score(x[1], x[2], max_tfidf, 5), reverse=True)]
    return ranked_result


# utils
def get_candidate(index_map: dict[str, dict], query: str):
    if len(query) <= 2:
        return index_map.get(query, {})
    gram_candidates = []
    gram_candidates_tfidf = []
    for i in range(len(query)-1):
        gram = query[i:i+2]
        gram_candidates.append(set(index_map.get(gram, {}).keys()))
        gram_candidates_tfidf.append(index_map.get(gram, {}))
    candidate_ids = set.intersection(*gram_candidates)
    candidate_id_tfidf = {id: sum([dic[id] for dic in gram_candidates_tfidf]) for id in candidate_ids}
    return candidate_id_tfidf


def calc_score(score, tfidf, max_tfidf, tfidf_weight):
    return score + tfidf_weight * tfidf / max_tfidf
