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

# web
```shell
cd web
py manage.py migrate
py manage.py makemigrations music_app
py manage.py migrate
python manage.py import_data
python manage.py runserver
```