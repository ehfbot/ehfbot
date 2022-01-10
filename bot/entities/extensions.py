from bot.db import db
from pony.orm import *


class Upsert():
  @classmethod
  @db_session
  def upsert(cls, **attrs) -> db.Entity:
    entity = cls.get(**attrs)

    if entity is None:
      entity = cls(**attrs)

    db.commit()

    return entity
