from music_app.models import Singer, Song


# rank search_result
def calc_song_rule_score(song: Song, query: str) -> int:
    score = 0
    # song_name
    if query not in song.name:
        pass
    elif song.name == query:
        score += 20
    elif song.name.startswith(query):
        score += 18
    else:
        score += 16
    # singer_name
    for singer in song.singers.all():
        if query not in singer.name:
            pass
        elif singer.name == query:
            score += 7
        elif singer.name.startswith(query):
            score += 5
        else:
            score += 3
    # lyrics
    if query in song.lyrics_text:
        score += 1
    return score


def calc_singer_rule_score(singer: Singer, query: str) -> int:
    score = 0
    # name
    if singer.name == query:
        score += 10
    if singer.name.startswith(query):
        score += 8
    elif query in singer.name:
        score += 6
    # info
    if query in singer.info_text:
        score += 1
    return score
