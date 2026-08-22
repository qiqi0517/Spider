import logging

logger = logging.getLogger("spider")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler("spider.log", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)