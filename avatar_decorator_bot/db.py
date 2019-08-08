from avatar_decorator_bot import config

import urllib.parse
from peewee import *

if config.DATABASE_URL.startswith('pg://') or config.DATABASE_URL.startswith('postgres://'):
    url = urllib.parse.urlparse(config.DATABASE_URL)
    database = PostgresqlDatabase(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
else:
    database = SqliteDatabase(config.DATABASE_URL)


class Color(Model):
    class Meta:
        database = database
    name = CharField(unique=True)
    r = IntegerField(constraints=[Check('r >= 0 and r < 256')])
    g = IntegerField(constraints=[Check('g >= 0 and g < 256')])
    b = IntegerField(constraints=[Check('b >= 0 and b < 256')])
    active = BooleanField(default=True)


class LastUserChoice(Model):
    class Meta:
        database = database
    user_id = IntegerField(unique=True)
    color = ForeignKeyField(model=Color, on_delete='CASCADE')


def initialize_database():
    database.connect()
    Color.create_table(safe=True)
    LastUserChoice.create_table(safe=True)
