Running locally with polling
----------------------------

1. Create file `bot.ini` with following content:

```ini
[Common]
DATABASE_URL = '/tmp/avatar-decorator-bot.sqlite'  # Or wherever you want to put your database
TOKEN = 'your-token-from-@BotFather'
USE_WEBHOOK = no
```

2. Create virtualenv and install dependencies:

```bash
python3 -m virtualenv venv -p python3 && source ./venv/bin/activate && python -m pip install -r requirements.txt
```

3. Run tests:

```bash
python -m nose .
```

3. Run bot in the current console:

```bash
python main.py
```

Running on Heroku
-----------------

1. Initialize an app:

```bash
heroku login && heroku create && heroku addons:create heroku-postgresql:hobby-dev
```

2. Set environment variables:

```bash
heroku config:set TOKEN=your-token-from-@BotFather
heroku config:set WEBHOOK_URL=$(heroku info -s | grep web_url | cut -d= -f2)
```

3. Deploy:

```bash
git push heroku master && heroku ps:scale web=1
```
