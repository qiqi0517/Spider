import json
import re
from pathlib import Path
import jieba
from . import config

def load_from_json_dict(file: Path) -> list[dict]:
    """Load a UTF-8 JSON dictionary and return its record values."""
    if not file.is_file():
        raise FileNotFoundError(f"JSON data file does not exist: {file}")
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise RuntimeError(f"failed to load JSON data from {file}: {e}") from e
    records = list(data.values())
    return records


def load_stopwords() -> set[str]:
    """Load non-empty stopwords from a UTF-8 text file."""
    with open(config.STOPWORDS_PATH, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def clean_lyrics(lyrics: list[str]) -> str:
    """Remove lyric metadata, blank lines, and exact duplicate lines."""
    valid_lines = []
    seen_lines = set()
    for line in lyrics:
        line = line.strip()
        if line == "" or\
            "：" in line or\
            " - " in line or\
            line in seen_lines:
            continue
        valid_lines.append(line)
        seen_lines.add(line)
    return "\n".join(valid_lines)


def tokenize(text: str, stopwords: set[str]) -> list[str]:
    """Tokenize text and remove stopwords, symbols, and trivial short tokens."""
    if not text:
        return []
    text = re.sub(r"\s+", " ", text).lower()
    text = re.sub(r"[，。！？；：、,.!?;:（）()\[\]【】“”‘’…—_/]+", " ", text)
    words = jieba.lcut(text, cut_all=False, HMM=True)
    tokens = []
    for word in words:
        word = word.strip()
        if not word or\
            word in stopwords or\
            not any(char.isalnum() for char in word) or\
            word.isdigit():
            continue
        tokens.append(word)
    return tokens

