import config, crawler, pipeline, get_local_config
from logger import logger

def run():
    get_local_config.get_local_config()
    crawler.get_music_data()
    crawler.get_images()

    
if __name__ == "__main__":
    run()