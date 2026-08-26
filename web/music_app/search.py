import time
from django.conf import settings
from music_app.models import Singer, Song
from music_app import config, rank, pipeline

INDEX_PATH = settings.BASE_DIR / "data"

# search via index_map
def search_songs(query: str):
    start_time = time.time()
    candidate_id_tfidf = get_candidate(config.SONG_INDEX, query)
    # verify cadidate and rank
    candidate_songs = Song.objects.filter(id__in = candidate_id_tfidf.keys()).prefetch_related("singers")
    search_result = []
    max_tfidf = 0
    for song in candidate_songs:
        tfidf = candidate_id_tfidf[song.id]
        rule_score = rank.calc_song_rule_score(song, query)
        if rule_score > 0:
            search_result.append((song, rule_score, tfidf))
            max_tfidf = max(tfidf, max_tfidf)
    ranked_result = [x[0] for x in sorted(search_result, key = lambda x: calc_score(x[1], x[2], max_tfidf, 5), reverse=True)]
    end_time = time.time()
    return ranked_result, end_time - start_time


def search_singers(query: str):
    start_time = time.time()
    candidate_id_tfidf = get_candidate(config.SINGER_INDEX, query)
    # verify cadidate and rank
    candidate_singers = Singer.objects.filter(id__in = candidate_id_tfidf.keys())
    search_result = []
    max_tfidf = 0
    for singer in candidate_singers:
        tfidf = candidate_id_tfidf[singer.id]
        rule_score = rank.calc_singer_rule_score(singer, query)
        if rule_score > 0:
            search_result.append((singer, rule_score, tfidf))
            max_tfidf = max(tfidf, max_tfidf)
    ranked_result = [x[0] for x in sorted(search_result, key = lambda x: calc_score(x[1], x[2], max_tfidf, 5), reverse=True)]
    end_time = time.time()
    return ranked_result, end_time - start_time



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
