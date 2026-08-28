import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import pandas as pd
import config, utils
from logger import logger

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

NIGHT_HOURS = {20, 21, 22, 23, 0}
HOURS = list(range(24))
NORMAL_COLOR = "#4C78A8"
HIGHLIGHT_COLOR = "#F58518"

def analyse_comment_hours():
    song_data = utils.load_from_json_dict(config.SONG_DATA_PATH)
    # get data
    hour_counts = [0] * 24
    invalid_comment = 0
    for song in song_data:
        for comment in song["comments"]:
            if comment["text"].strip() == "":
                invalid_comment += 1
                continue
            try:
                comment_hour = int(comment["time"]["hour"])
            except (KeyError, TypeError, ValueError):
                invalid_comment += 1
                continue
            if not 0 <= comment_hour <= 23:
                invalid_comment += 1
                continue
            hour_counts[comment_hour] += 1

    # analyse
    valid_comment = sum(hour_counts)
    night_comment = sum(hour_counts[hour] for hour in NIGHT_HOURS)
    night_ratio = night_comment / valid_comment
    peak_hour = max(HOURS, key=lambda hour: hour_counts[hour])
    peak_cnt = hour_counts[peak_hour]
    if invalid_comment > 0:
        logger.warning(f"got {invalid_comment} invalid comments")
    logger.info(f"got {valid_comment} valid_comments, {night_comment} night_comments")
    assert sum(hour_counts) == valid_comment
    assert 0 <= night_ratio <= 1
    assert 0 <= peak_hour <= 23

    # save csv
    hour_counts_df = pd.DataFrame({
        "hours": HOURS,
        "comments": hour_counts,
    })
    COMMENT_TIME_OUTPUT_DIR = config.OUTPUT_DIR / "comment_time"
    COMMENT_TIME_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    hour_counts_df.to_csv(COMMENT_TIME_OUTPUT_DIR / "comment_hour_counts.csv", index=False, encoding="utf-8")
    logger.info(".csv saved")

    # plot
    fig, ax = plt.subplots(figsize=(12, 6))
    bar_colors = [HIGHLIGHT_COLOR if hour in NIGHT_HOURS else NORMAL_COLOR for hour in HOURS]
    bars = ax.bar(HOURS, hour_counts, color=bar_colors, width=0.8)
    ax.set_title("热门评论发布时间分布", fontsize=16)
    ax.set_xlabel("评论发布时间（小时）")
    ax.set_ylabel("评论数量")
    ax.set_xticks(HOURS)
    ax.set_xlim(-0.7, 23.7)
    # horizontal grid
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    # upper_left legend to show bar colors
    ax.legend(
        handles = [
            Patch(color=NORMAL_COLOR, label="其他时段"),
            Patch(color=HIGHLIGHT_COLOR, label="20:00 至次日 00:59"),
        ],
        loc = "upper center",
        ncol = 2,
    )
    # annotate peak_bar
    peak_bar = bars[peak_hour]
    ax.annotate(
        f"峰值：{peak_hour}点，共{peak_cnt}条",
        xy = (peak_bar.get_x() + peak_bar.get_width()/2, peak_cnt),
        xytext = (12, -12),
        textcoords = "offset points", 
        ha = "left", va = "top",
        fontsize = 10,
    )
    # axis illustration
    ax.text(
        0.98, 0.95,
        ("晚间（20:00 至次日 00:59）\n"
         f"评论占比：{night_ratio:.2%}"),
        transform = ax.transAxes,
        ha = "right", va = "top",
        bbox = {
            "boxstyle": "round",
            "facecolor": "white",
            "edgecolor": "gray",
            "alpha": 0.85,
        },
    )
    # figure illustration
    fig.text(
        0.5, 0.02,
        "注：以上图表仅基于从 QQ 音乐抓取的少量热门评论",
        ha = "center", 
        fontsize = 9,
        color = "dimgray"
    )
    # save plot
    fig.savefig(COMMENT_TIME_OUTPUT_DIR / "comment_hour_distribution.png", dpi=300, bbox_inches="tight")
    logger.info(".png saved")
    # release memory
    plt.close(fig)

    # save info
    comment_time_info = {
        "hour_counts": hour_counts,
        "valid_comment_count": valid_comment,
        "invalid_comment_count": invalid_comment,
        "night_comment_count": night_comment,
        "night_ratio": night_ratio,
        "peak_hour": peak_hour,
        "peak_count": peak_cnt,
        "csv_path": str(COMMENT_TIME_OUTPUT_DIR / "comment_hour_counts.csv"),
        "plot_path": str(COMMENT_TIME_OUTPUT_DIR / "comment_hour_distribution.png"),
    }
    utils.save_to_json(COMMENT_TIME_OUTPUT_DIR / "comment_time_info.json", comment_time_info)
    return comment_time_info
