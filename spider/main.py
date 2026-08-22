import config, crawler, pipeline
from logger import logger

def run():
    crawler.get_music_data()
    crawler.get_images()

    
if __name__ == "__main__":
    run()