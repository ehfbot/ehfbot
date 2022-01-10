from __future__ import annotations

from datetime import date, datetime

import discord
from bot.db import db
from discord.ext import commands
from discord.utils import get
from pony.orm import *

from .extensions import Upsert
from .postcount import Postcount


class User(db.Entity, Upsert):
    _table_ = "users"
    id = PrimaryKey(int, auto=True)
    external_id = Required(int, unique=True, size=64)
    messages_count = Optional(int)
    last_posted_at = Optional(datetime)
    postcounts = Set('Postcount', reverse='user')


    @classmethod
    @db_session
    def posted(cls, message=discord.Message) -> None:
        user = cls.upsert(external_id=message.author.id)

        if user is None:
            raise

        if user.messages_count is None:
            user.messages_count = 0

        user.last_posted_at = datetime.now()
        user.messages_count += 1

        postcount = Postcount.upsert(user=user, date=date.today())

        if postcount.messages_count is None:
            postcount.messages_count = 0

        postcount.messages_count += 1

        db.commit()
