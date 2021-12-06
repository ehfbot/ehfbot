from datetime import datetime

import discord
from bot.db import db
from discord.ext import commands
from discord.utils import get
from pony.orm import *

# from pony import Optional, PrimaryKey, Required


class User(db.Entity):
  _table_ = 'users'
  id = PrimaryKey(int, auto=True)
  external_id = Required(int, unique=True)
  messages_count = Optional(int)
  last_posted_at = Optional(datetime)

  @classmethod
  def posted(cls, external_id = int):
    user = cls.upsert(external_id = external_id)
    if user.messages_count is None:
      user.messages_count = 0
    user.messages_count += 1
    user.save()
    next
