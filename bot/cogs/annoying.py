import re

import discord
from discord.ext import commands

from .. import helper


class AnnoyingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        message_content = message.content.lower()
        if re.match(r'^[^\w]?(yo)?ur mom.*$', message_content): await message.delete()

        wsw_words = ["phone", "sex", "horny", "whore", "fuck", "trash", "fucking", "ugly", "butterface", "attention", "sugar daddy", "sugar", "daddy", "thot", "pussy", "rape", "dick", "blow", "blowjob", "suck", "of", "onlyfans", "whatsapp"]
        if any(word in message_content for word in wsw_words): await message.delete()
