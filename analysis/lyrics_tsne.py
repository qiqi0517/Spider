import matplotlib
matplotlib.use("Agg")

from collections import Counter
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import config, utils
from logger import logger

MIN_LYRIC_LENGTH = 30
LYRICS_CHUNK_MAX_LENGTH = 300
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
BATCH_SIZE = 32
NUM_CLUSTERS = 32
CLUSTER_NAMES = [
    "追梦励志",
    "多语舞曲",
    "一生情歌",
    "甜蜜告白",
    "山河侠义",
    "星空浪漫",
    "古风相思",
    "版权声明",
    "失恋遗忘",
    "故乡旅途",
    "英语情感冲突",
    "异乡漂泊",
    "英语回忆陪伴",
    "季节离别",
    "情感拉扯",
    "韩语抒情",
    "日语青春",
    "说唱态度",
    "粤语情感",
    "暧昧说唱",
    "少年梦想",
    "雨夜思念",
    "韩语恋爱",
    "英语说唱",
    "青春回忆",
    "韩语舞曲",
    "海洋离别",
    "爱而不得",
    "暗恋告白",
    "成熟情歌",
    "关系犹豫",
    "青春成长",
]
CLUSTER_COLORS: list[str] = [
    "#1F77B4",  # 蓝
    "#FF7F0E",  # 橙
    "#2CA02C",  # 绿
    "#D62728",  # 红
    "#9467BD",  # 紫
    "#8C564B",  # 棕
    "#E377C2",  # 粉
    "#7F7F7F",  # 灰
    "#BCBD22",  # 黄绿
    "#17BECF",  # 青
    "#393B79",  # 深蓝紫
    "#637939",  # 深橄榄绿
    "#8C6D31",  # 深黄棕
    "#843C39",  # 深砖红
    "#7B4173",  # 深紫红
    "#3182BD",  # 湖蓝
    "#E6550D",  # 深橙
    "#31A354",  # 翠绿
    "#756BB1",  # 蓝紫
    "#636363",  # 深灰
    "#6B6ECF",  # 靛蓝
    "#8CA252",  # 草绿
    "#BD9E39",  # 金褐
    "#AD494A",  # 暗红
    "#A55194",  # 紫红
    "#6BAED6",  # 浅蓝
    "#FD8D3C",  # 浅橙
    "#74C476",  # 浅绿
    "#9E9AC8",  # 浅紫
    "#969696",  # 中灰
    "#CE6DBD",  # 洋红
    "#9C9EDE",  # 淡蓝紫
]


def analyse_lyrics_tsne():
    # build documents
    songs = utils.load_from_json_dict(config.SONG_DATA_PATH)
    stopwords = utils.load_stopwords()
    documents = []
    invalid_lyrics = 0
    for song in songs:
        # clean lyrics
        lyrics = utils.clean_lyrics(song["lyrics"])
        lyrics_length = len(lyrics.replace("\n", "").strip())
        if lyrics_length < MIN_LYRIC_LENGTH:
            invalid_lyrics += 1
            continue
        # tokenize
        tokens = utils.tokenize(lyrics, stopwords)
        if tokens == []:
            invalid_lyrics += 1
            continue
        # save info
        document = {
            "url": song["url"],
            "name": song["song_name"],
            "singers": [singer["name"] for singer in song["singer"]],
            "lyrics": lyrics,
            "tokens": tokens,
        }
        documents.append(document)
    document_cnt = len(documents)
    logger.info(f"got {document_cnt} valid_documents, {invalid_lyrics} invalid_lyrics")
    
    # embed
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBEDDING_MODEL)
    logger.info(f"loaded model {EMBEDDING_MODEL}")

    # prepare embedding_input
    all_chunks = []
    chunk_song_idx = []
    song_chunk_cnt = [0] * len(documents)
    invalid_chunks = 0
    for song_idx, document in enumerate(documents):
        song_chunks = split_lyrics(document["lyrics"])
        if song_chunks == []:
            invalid_chunks += 1
            continue
        all_chunks.extend(song_chunks)
        chunk_song_idx.extend([song_idx]*len(song_chunks))
        song_chunk_cnt[song_idx] = len(song_chunks)
    logger.info(f"complete embedding_input preparation, got {len(all_chunks)} valid chunks, {invalid_chunks} invalid chunks")
    # embed each chunk
    chunk_embeddings = model.encode(
        all_chunks,
        batch_size = BATCH_SIZE,
        show_progress_bar = True,
        normalize_embeddings = True,
        convert_to_numpy = True,
    )
    embed_dim = chunk_embeddings.shape[1]
    logger.info(f"succeed in embedding chunks, generating chunk_embeddings of shape {chunk_embeddings.shape}")
    # merge chunks of same song
    chunk_song_idx = np.array(chunk_song_idx, dtype=int)
    song_chunk_cnt = np.array(song_chunk_cnt, dtype=int)
    assert not any(song_chunk_cnt <= 0)
    song_embeddings = np.zeros_like(chunk_embeddings, shape=(document_cnt, embed_dim))
    for chunk_embedding, song_idx in zip(chunk_embeddings, chunk_song_idx):
        song_embeddings[song_idx] += chunk_embedding
    song_embeddings /= song_chunk_cnt[:, None]
    norms = np.linalg.norm(song_embeddings, axis=1, keepdims=True)
    song_embeddings /= norms
    logger.info(f"succeed in merging song_chunks, generating song_embeddings of shape {song_embeddings.shape}")
    assert song_embeddings.shape[0] == document_cnt
    assert np.isfinite(song_embeddings).all()

    # KMeans cluster
    kmeans = KMeans(n_clusters=NUM_CLUSTERS, n_init=10, random_state=config.SEED)
    labels = kmeans.fit_predict(song_embeddings)
    cluster_cnts = np.bincount(labels, minlength=NUM_CLUSTERS)
    for i, count in enumerate(cluster_cnts):
        message = f"theme {i} got {count} songs ({100*count/document_cnt:.2f}%)"
        if count < 0.01*document_cnt:
            logger.warning(message)
        else:
            logger.info(message)
    for document_id, document in enumerate(documents):
        document["cluster_id"] = labels[document_id]

    # extract cluster key_word
    cluster_summaries = []
    token_counters = []
    for cluster_id in range(NUM_CLUSTERS):
        document_ids = np.flatnonzero(labels==cluster_id)
        token_counter = Counter()
        singer_counter = Counter()
        for document_id in document_ids:
            document = documents[document_id]
            token_counter.update(document["tokens"])
            singer_counter.update(document["singers"])
        token_counters.append(token_counter)
        keywords = [word for word, cnt in token_counter.most_common(10)]
        distances = np.linalg.norm(
            song_embeddings[document_ids] - kmeans.cluster_centers_[cluster_id],
            axis=1,
        )
        example_ids = document_ids[np.argsort(distances)[:10]]
        example_songs = [documents[document_id]["name"] for document_id in example_ids]
        logger.info(f"cluster_{cluster_id} has keywords {keywords}")
        summary = {
            "cluster_id": cluster_id,
            "cluster_name": CLUSTER_NAMES[cluster_id],
            "song_cnt": len(document_ids),
            "singer_cnt": len(singer_counter),
            "keywords": keywords,
            "example_songs": example_songs,
            "common_singers": singer_counter.most_common(5),
            "common_token": token_counter.most_common(5),
        }
        cluster_summaries.append(summary)


    # t-SNE
    tsne = TSNE(
        n_components = 2,
        perplexity = min(30, document_cnt),
        random_state = config.SEED,
        init = "pca",
        learning_rate = "auto",
    )
    song_coordinates = tsne.fit_transform(song_embeddings)
    logger.info("complete t-SNE")
    assert len(labels) == document_cnt
    assert song_coordinates.shape == (document_cnt, 2)
    assert sum(summary["song_cnt"] for summary in cluster_summaries) == document_cnt
    for document_id, document in enumerate(documents):
        document["x"] = song_coordinates[document_id, 0]
        document["y"] = song_coordinates[document_id, 1]

    # create data_form & save results
    TSNE_OUTPUT_DIR = config.OUTPUT_DIR / "lyrics_tsne"
    TSNE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # csv
    document_df = pd.DataFrame(documents)
    document_df.to_csv(TSNE_OUTPUT_DIR / "lyrics_tsne_documents.csv", index=False, encoding="utf-8")
    cluster_df = pd.DataFrame(cluster_summaries)
    cluster_df.to_csv(TSNE_OUTPUT_DIR / "lyrics_tsne_clusters.csv", index=False, encoding="utf-8")
    # t-SNE plot
    fig, ax = plt.subplots(figsize=(14, 8))
    chinese_font = FontProperties(fname=str(config.FONT_PATH))
    for cluster_id in range(NUM_CLUSTERS):
        mask = (labels == cluster_id)
        ax.scatter(
            x = song_coordinates[mask, 0],
            y = song_coordinates[mask, 1],
            s = 18,
            alpha = 0.65,
            color = CLUSTER_COLORS[cluster_id],
            label = CLUSTER_NAMES[cluster_id],
        )
    ax.set_title("歌词主题聚类 t-SNE可视化", fontproperties=chinese_font, fontsize=16)
    ax.legend(
        prop=chinese_font,
        title="主题",
        title_fontproperties=chinese_font,
        loc="upper right",
        ncol=2,
    )
    ax.grid(linestyle="--", alpha=0.2)
    fig.tight_layout()
    fig.savefig(TSNE_OUTPUT_DIR / "lyrics_theme_tsne.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"data saved!")
    return {
        "document_cnt": document_cnt,
        "invalid_lyrics": invalid_lyrics,
        "chunk_cnt": len(all_chunks),
        "embedding_dim": embed_dim,
        "cluster_summaries": cluster_summaries,
    }


def split_lyrics(lyrics: str) -> list[str]:
    lines = [line.strip() for line in lyrics.splitlines() if line.strip()!=""]
    chunks = []
    current_chunk = ""
    for line in lines:
        if len(line) > LYRICS_CHUNK_MAX_LENGTH:
            # save current_chunk
            if len(current_chunk) > 0:
                chunks.append(current_chunk[:-1])
                current_chunk = ""
            # split line
            for start_idx in range(0, len(line), LYRICS_CHUNK_MAX_LENGTH):
                chunk = line[start_idx: start_idx+LYRICS_CHUNK_MAX_LENGTH]
                if chunk != "":
                    chunks.append(chunk)
        else:
            new_length = len(current_chunk) + len(line) + 1 # \n
            if new_length > LYRICS_CHUNK_MAX_LENGTH:
                chunks.append(current_chunk[:-1])
                current_chunk = line + "\n"
            else:
                current_chunk += (line + "\n")
    if current_chunk != "":
        chunks.append(current_chunk[:-1])
    return chunks
