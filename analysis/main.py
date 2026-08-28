import comment_time, wordcloud_analyse, lyrics_tsne

def run() -> None:
    comment_time.analyse_comment_hours()
    wordcloud_analyse.anaylyse_wordcloud()


if __name__ == "__main__":
    run()
