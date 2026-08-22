import logging
from music_app.management.commands import config

logger = logging.getLogger("data_loader")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler(
    config.LOG_PATH / "data_loader.log", 
    encoding="utf-8"
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)