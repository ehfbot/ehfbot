from __future__ import annotations

from datetime import date, datetime

import discord
from bot.db import db
from discord.ext import commands
from discord.utils import get
from pony.orm import *

from .extensions import Upsert


class Postcount(db.Entity, Upsert):
  _table_ = 'postcounts'
  id = PrimaryKey(int, auto=True)
  user = Required('User')
  date = Required(date)
  messages_count = Required(int)
  messages_sent = Set('Message', reverse='user_from')
