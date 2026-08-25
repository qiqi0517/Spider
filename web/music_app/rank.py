from music_app.models import Singer, Song
from music_app import config

# rank search_result
def calc_song_score(song: Song, query):
    score = 0
    # song_name
    if song.name == query:
        score += 20
    elif song.name.startswith(query):
        score += 18
    elif query in song.name:
        score += 16
    # singer_name
    for singer in song.singers.all():
        if singer.name == query:
            score += 7
        elif singer.name.startswith(query):
            score += 5
        elif query in singer.name:
            score += 3
    # lyrics
    if query in song.lyrics:
        score += 1
    return score
    



def calc_singer_score(singer: Singer, query):
    score = 0
    # name
    if singer.name == query:
        score += 10
    if singer.name.startswith(query):
        score += 8
    elif query in singer.name:
        score += 6
    # info
    if query in singer.info:
        score += 2
    return score