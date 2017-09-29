Running locally with polling
----------------------------

1. Create file `bot.ini` with following content:

    [Common]
    DATABASE_URL = '/tmp/avatar-decorator-bot.sqlite'  # Or wherever you want to put your database
    TOKEN = 'your-token-from-@BotFather'
    USE_WEBHOOK = no

2. Create virtualenv and install dependencies:

    virtualenv -p python3 venv && source ./venv/bin/activate && pip install -r requirements.txt

3. Run bot in current console:

    python bot.py

Running on Heroku
-----------------

1. Initialize an app:

    heroku login && heroku create && heroku addons:create heroku-postgresql:hobby-dev

2. Set environment variables:

    heroku config:set TOKEN=your-token-from-@BotFather
    heroku config:set WEBHOOK_URL=$(heroku info -s | grep web_url | cut -d= -f2)

3. Deploy:

    git push heroku master && heroku ps:scale web=1