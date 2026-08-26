# spider
local data: 
    - config_local.py
    - cookies.json
    - qq_state.json
sign in qqMusic to get cookies, then save in config_local.COOKIE
```shell
cd spider
python main.py
```

## Web 音乐信息系统

### 环境要求

- Python 3.10 或更高版本
- 项目依赖见根目录的 `requirements.txt`

建议使用 Conda 创建独立的 Python 3.10 虚拟环境。在项目根目录执行：

```powershell
conda create --name spider python=3.10
conda activate spider
conda install --channel conda-forge --file requirements.txt
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