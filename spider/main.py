import config
import crawler
import get_local_config
import pipeline
from logger import logger


def run() -> None:
    """Run text crawling followed by image downloading."""
    if not config.QQ_STATE_PATH.exists() or not config.COOKIES_PATH.exists():
        raise FileNotFoundError(
            "Local login config is missing. Run 'python get_local_config.py' first."
        )
    crawler.get_music_data()
    crawler.get_images()


if __name__ == "__main__":
    run()
