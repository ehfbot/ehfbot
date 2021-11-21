import re

import discord
from discord.ext import commands

from .. import helper


class AnnoyingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if re.match(r'^[^\w]?(yo)?ur mom.*$', message.content, re.IGNORECASE): await message.delete()
        if re.match(r'.*meg.*', message.content, re.IGNORECASE): await message.delete()
        if re.match(r'^Lol$', message.content): await message.delete()
