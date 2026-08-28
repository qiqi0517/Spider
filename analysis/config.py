from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SONG_DATA_PATH = BASE_DIR / "data" / "raw" / "song_list.json"
ANALYSIS_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ANALYSIS_DIR / "output"
STOPWORDS_PATH = ANALYSIS_DIR / "resources" / "stopwords_zh.txt"
FONT_PATH = Path(r"C:\Windows\Fonts\msyh.ttc")
LOG_PATH = BASE_DIR / "logs"