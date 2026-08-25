import logging
from music_app.management.commands.build_inverted_index_utils import config

logger = logging.getLogger("index_builder")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler(
    config.LOG_PATH / "index_builder.log", 
    encoding="utf-8"
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)