import matplotlib
matplotlib.use("Agg")

from collections import Counter
from wordcloud import WordCloud
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.axes import Axes
import config, utils
from logger import logger

def anaylyse_wordcloud():
    songs = utils.load_from_json_dict(config.SONG_DATA_PATH)
    stopwords = utils.load_stopwords()
    # count words
    lyrics_counter = Counter()
    comments_counter = Counter()
    invalid_lyrics = invalid_comments = valid_lyrics = valid_comments = 0
    for song in songs:
        # count lyrics
        lyrics = song["lyrics"]
        cleaned_lyrics = utils.clean_lyrics(lyrics)
        if cleaned_lyrics == "":
            invalid_lyrics += 1
        else:
            tokens = utils.tokenize(cleaned_lyrics, stopwords)
            if tokens == []:
                invalid_lyrics += 1
            else:
                lyrics_counter.update(tokens)
                valid_lyrics += 1
        # count comments
        for comment in song["comments"]:
            comment_text = comment["text"].strip()
            if comment_text == "":
                invalid_comments += 1
                continue
            tokens = utils.tokenize(comment_text, stopwords)
            if tokens == []:
                invalid_comments += 1
                continue
            comments_counter.update(tokens)
            valid_comments += 1

    # analyse
    lyrics_unique_tokens = len(lyrics_counter)
    comments_unique_tokens = len(comments_counter)
    lyrics_total_tokens = sum(lyrics_counter.values())
    comments_total_tokens = sum(comments_counter.values())
    if invalid_lyrics > 0 or invalid_comments > 0:
        logger.warning(f"{invalid_lyrics} invalid_lyrics, {invalid_comments} invalid_comments")
    logger.info(f"{valid_lyrics} valid_lyrics, {valid_comments} valid_comments")
    logger.info(f"lyrics: {lyrics_unique_tokens} different tokens, totally {lyrics_total_tokens} appearences")
    logger.info(f"comments: {comments_unique_tokens} different tokens, totally {comments_total_tokens} appearences")
    
    # save to csv
    WORDCLOUD_OUTPUT_DIR = config.OUTPUT_DIR / "wordcloud"
    lyrics_counter_df = create_counter_dataframe(lyrics_counter, lyrics_total_tokens, WORDCLOUD_OUTPUT_DIR / "lyrics_counter.csv")
    comments_counter_df = create_counter_dataframe(comments_counter, comments_total_tokens, WORDCLOUD_OUTPUT_DIR / "comments_counter.csv")
    logger.info(".csv saved")

    # generate wordcloud
    lyrics_frequencies = lyrics_counter_df.set_index("token")["count_per_1w"].to_dict()
    comments_frequencies = comments_counter_df.set_index("token")["count_per_1w"].to_dict()
    lyrics_wordcloud = create_wordcloud(lyrics_frequencies, "Blues")
    comments_wordcloud = create_wordcloud(comments_frequencies, "Oranges")

    # draw wordcloud
    fig, ax = plt.subplots(1, 2, figsize=(16, 8))
    show_wordcloud(lyrics_wordcloud, title="歌词词云图", ax=ax[0])
    show_wordcloud(comments_wordcloud, title="评论词云图", ax=ax[1])
    fig.tight_layout()

    # save wordcloud
    fig.savefig(WORDCLOUD_OUTPUT_DIR / "wordcloud.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.info(".png saved")

    # save info
    wordcloud_info = {
        "lyrics_counter": lyrics_counter,
        "comments_counter": comments_counter,
        "valid_lyrics": valid_lyrics,
        "invalid_lyrics": invalid_lyrics,
        "valid_comments": valid_comments,
        "invalid_comments": invalid_comments,
        "lyrics_unique_tokens": lyrics_unique_tokens,
        "comments_unique_tokens": comments_unique_tokens,
        "lyrics_total_tokens": lyrics_total_tokens,
        "comments_total_tokens": comments_total_tokens,
    }
    utils.save_to_json(WORDCLOUD_OUTPUT_DIR / "wordcloud_info.json", wordcloud_info)


def create_wordcloud(frequencies, colormap):
    cloud = WordCloud(
        font_path = str(config.FONT_PATH),
        width=1000, height=800,
        background_color="white",
        max_words=150,
        colormap=colormap,
        random_state=config.SEED,
    )
    return cloud.generate_from_frequencies(frequencies)


def show_wordcloud(wordcloud: WordCloud, title: str, ax: Axes):
    title_font = FontProperties(fname=str(config.FONT_PATH))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.set_title(title, fontproperties=title_font, fontsize=20)
    ax.axis("off")
    logger.info(f"drawn wordcloud {title}")



def create_counter_dataframe(counter: Counter, total_tokens, file: Path):
    counter_df = pd.DataFrame(
        counter.most_common(),
        columns=["token", "count"],
    )
    counter_df["count_per_1w"] = 10_000 * counter_df["count"] / total_tokens
    file.parent.mkdir(parents=True, exist_ok=True)
    counter_df.to_csv(file, index=False, encoding="utf-8")
    return counter_df
