from pony import orm

from bot.env import env

db = orm.Database()
db.bind(provider=env['DATABASE_PROVIDER'], user=env['DATABASE_USER'], password=env['DATABASE_PASSWORD'], host=env['DATABASE_HOST'], database=env['DATABASE_NAME'])
