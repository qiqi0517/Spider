# Python大作业 - 爬虫与信息系统 - 2026.08

## spider 爬虫部分

### 环境要求

爬虫使用 Playwright 获取动态页面。建议使用 Conda 创建独立环境，并安装项目依赖和
Playwright 所需的 Chromium 浏览器。在项目根目录执行：

```powershell
conda create --name spider python=3.10
conda activate spider
python -m pip install -r requirements.txt
playwright install chromium
```

首次运行时，先生成本地登录配置：

```powershell
cd spider
python get_local_config.py
```

命令会打开可见的 QQ 音乐页面。完成登录后返回终端并按 Enter，程序会在
`spider/local_config/` 下生成 `cookies.json` 和 `qq_state.json`。这些文件包含个人登录
信息，已被 Git 忽略，请勿提交或分享。

登录配置生成后运行爬虫：

```powershell
python main.py
```

后续运行不需要重复登录；仅当登录状态失效或两个配置文件缺失时，才重新执行
`python get_local_config.py`。

## Web 音乐信息系统

### 环境要求

- Python 3.10 或更高版本
- 项目依赖见根目录的 `requirements.txt`

建议使用 Conda 创建独立的 Python 3.10 虚拟环境。请确保已在项目根目录执行以下代码，配置环境：

```powershell
conda create --name spider python=3.10
conda activate spider
python -m pip install -r requirements.txt
```

后续每次重新打开终端时，先执行 `conda activate spider` 再运行项目命令。如果当前
PowerShell 无法使用 `conda activate`，请先执行 `conda init powershell`，重启
PowerShell 后再激活环境。

### 数据准备

首次初始化网站前，请确认爬虫已经生成下列本地数据：

```text
data/raw/singer_list.json
data/raw/song_list.json
data/image/singer/
data/image/song/
```

这些文件包含爬取结果，不会提交到 Git。如果文件不存在，请先按照上文的爬虫说明运行
爬虫。`web/db.sqlite3` 和 `web/data/*.json` 同样是可重新生成的本地文件。

### 首次初始化

在项目根目录执行：

```powershell
cd web
python manage.py migrate
python manage.py import_data
python manage.py build_inverted_index
python manage.py runserver
```

浏览器访问 <http://127.0.0.1:8000/>。

数据库迁移文件已经包含在仓库中，首次运行只需执行 `migrate`。仅在修改 Django 模型后
才需要运行 `python manage.py makemigrations music_app`，并应将新迁移文件提交到 Git。

### 日常启动

数据库和索引已经生成时，只需执行：

```powershell
cd web
python manage.py runserver
```

如果重新运行了 `import_data` 或修改了歌曲、歌手的可搜索字段，请重新执行：

```powershell
python manage.py build_inverted_index
```

索引由 Web 进程按需加载并缓存在内存中。运行中的服务器不会自动读取新索引，因此重建
索引后需要停止并重新启动 `runserver`。

## 数据分析

### 环境和输入数据

数据分析与爬虫、Web 共用根目录的 `requirements.txt` 和上文创建的 `spider` 环境。
分析代码使用下列第三方库：

- NumPy、Pandas：数据计算和 CSV 输出；
- Matplotlib：绘制评论时间柱状图和 t-SNE 散点图；
- jieba、WordCloud：中文分词和词云生成；
- scikit-learn：K-Means 聚类和 t-SNE 降维；
- Sentence Transformers、PyTorch：生成歌词语义向量。

运行前请确认以下文件存在：

```text
data/raw/song_list.json
analysis/resources/stopwords_zh.txt
```

分析图使用微软雅黑显示中文。Windows 默认字体路径为
`C:\Windows\Fonts\msyh.ttc`；如果系统中没有该字体，或在其他操作系统运行，请先在
`analysis/config.py` 中将 `FONT_PATH` 改为本机可用的中文字体文件路径。

歌词聚类首次运行时会从 Hugging Face 下载
`BAAI/bge-small-zh-v1.5` 模型，需要保持 VPN 直连模式并预留模型缓存空间。使用 CPU 也可以
完成，但生成歌词向量和 t-SNE 降维所需时间较长。安装完成后可先验证 PyTorch：

```powershell
python -c "import torch; print(torch.__version__); print(torch.rand(1))"
```

为避免 Windows 下出现 PyTorch DLL 或二进制依赖冲突，建议在新建的 Conda 环境中统一
使用 `python -m pip install -r requirements.txt`，不要再混用不同来源重复安装 PyTorch。

### 选择分析任务

`analysis/main.py` 中 `run()` 函数的三行调用分别对应三个分析任务：

```python
comment_time.analyse_comment_hours()
wordcloud_analyse.anaylyse_wordcloud()
lyrics_tsne.analyse_lyrics_tsne()
```

取消某行开头的 `#` 即可启用该任务；暂时不需要运行的任务可以注释。当前代码只启用了
歌词聚类任务。如果需要一次完成全部分析，应取消前两个调用的注释，使三行调用均生效。

### 运行分析

分析模块使用直接导入，因此必须进入 `analysis` 目录再运行 `main.py`：

```powershell
conda activate spider
cd analysis
python main.py
```

运行日志写入 `logs/analyser.log`。三项任务的输出如下：

| 分析任务 | 输出目录 | 主要结果 |
| --- | --- | --- |
| 热门评论发布时间 | `analysis/output/comment_time/` | 每小时评论数 CSV、统计信息 JSON、柱状图 PNG |
| 歌词与评论词云 | `analysis/output/wordcloud/` | 两类词频 CSV、统计信息 JSON、词云 PNG |
| 歌词语义聚类 | `analysis/output/lyrics_tsne/` | 歌曲聚类 CSV、聚类摘要 CSV、t-SNE 散点图 PNG |

程序会自动创建不存在的输出目录；重复运行同一任务时，同名结果文件会被新结果覆盖。
