import time

import discord
from bot.entities import User
from discord.ext import commands
from discord.utils import get


class PostingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_posting_times = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
      external_id = message.author.id
      last_posted_at = self.user_posting_times.get(external_id)

      if last_posted_at is None or time.time() - last_posted_at > 30: # cooldown in seconds
        User.posted(message = message)
        self.user_posting_times[external_id] = time.time()

      return None
