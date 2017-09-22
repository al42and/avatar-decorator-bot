import config
from peewee import *

database = SqliteDatabase(config.SQLITE_FILE)


class Color(Model):
    class Meta:
        database = database
    name = CharField(unique=True)
    r = IntegerField(constraints=[Check('r >= 0 and r < 256')])
    g = IntegerField(constraints=[Check('g >= 0 and g < 256')])
    b = IntegerField(constraints=[Check('b >= 0 and b < 256')])


class LastUserChoice(Model):
    class Meta:
        database = database

    user_id = IntegerField(unique=True)
    color = ForeignKeyField(rel_model=Color, on_delete='CASCADE')


def initialize_database():
    database.connect()
    Color.create_table(fail_silently=True)
    LastUserChoice.create_table(fail_silently=True)
