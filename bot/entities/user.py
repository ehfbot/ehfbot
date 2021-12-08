from __future__ import annotations

from datetime import datetime

import discord
from bot.db import db
from discord.ext import commands
from discord.utils import get
from pony.orm import *


class User(db.Entity):
  _table_ = 'users'
  id = PrimaryKey(int, auto=True)
  external_id = Required(int, unique=True, size=64)
  messages_count = Optional(int)
  last_posted_at = Optional(datetime)

  @classmethod
  @db_session
  def upsert(cls, **attrs) -> User:
    user = cls.get(**attrs)

    if user is None:
      user = cls(*attrs)

    db.commit()

    return user

  @classmethod
  @db_session
  def posted(cls, message = discord.Message) -> None:
    user = cls.upsert(external_id = message.author.id)

    if user is None:
      raise

    user.last_posted_at = datetime.now()
    user.messages_count += 1

    db.commit()
