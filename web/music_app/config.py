from django.conf import settings
from music_app import pipeline

ITEM_PER_PAGE = 20

INDEX_PATH = settings.BASE_DIR / "data"
SONG_INDEX = pipeline.load_index(INDEX_PATH / "song_index.json")
SINGER_INDEX = pipeline.load_index(INDEX_PATH / "singer_index.json")