import logging
from pathlib import Path
import config

logger = logging.getLogger("spider")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_path = config.LOG_PATH / "spider.log"
file_handler = logging.FileHandler(log_path, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
