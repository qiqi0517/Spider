from django.conf import settings

ITEM_PER_PAGE = 20
USER_COMMENT_MAX_LENGTH = 500
SEARCH_QUERY_MAX_LENGTH = 20
SEARCH_TIME_PLACEHOLDER = "SEARCH_TIME_PLACEHOLDER"

INDEX_PATH = settings.BASE_DIR / "data"
SONG_UNIGRAM_INDEX_PATH = INDEX_PATH / "song_unigram_index.json"
SONG_BIGRAM_INDEX_PATH = INDEX_PATH / "song_bigram_index.json"
SINGER_UNIGRAM_INDEX_PATH = INDEX_PATH / "singer_unigram_index.json"
SINGER_BIGRAM_INDEX_PATH = INDEX_PATH / "singer_bigram_index.json"
