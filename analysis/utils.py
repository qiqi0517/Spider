import json, re, os
from pathlib import Path
from collections import Counter
import pandas as pd
import jieba
import config
from logger import logger

def load_from_json_dict(file: Path) -> list[dict]:
    """Load a UTF-8 JSON dictionary and return its record values."""
    if not file.is_file():
        logger.error(f"JSON data file does not exist: {file}")
        raise FileNotFoundError(f"JSON data file does not exist: {file}")
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"failed to load JSON data from {file}: {e}")
        raise RuntimeError(f"failed to load JSON data from {file}: {e}") from e
    records = list(data.values())
    logger.info(f"succeed in looading json_data from {file}")
    return records


def save_to_json(file: Path, content: dict | list) -> None:
    """Save JSON data atomically to avoid leaving a partial output file."""
    file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = file.with_suffix(file.suffix + ".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, file)
    finally:
        if temp_file.exists():
            temp_file.unlink()


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
    logger.info(f"cleaned lyrics: {lyrics[:10]}...")
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
            word.isdigit() or\
            (len(word) == 1 and not re.fullmatch(r"[\u4e00-\u9fff]", word)):
            continue
        tokens.append(word)
    logger.info(f"tokenized text: {text[:10]}...")
    return tokens
