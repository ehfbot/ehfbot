import random

import discord
from discord.ext import commands

from .. import helper


class AnimeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if isinstance(message.channel, discord.TextChannel) and message.channel.name == self.bot.config['channels']['anime']:
            if random.randrange(0, 50) == 0:
                rand = random.choice([1, 2, 3])
                if rand == 1:
                    await message.add_reaction('🚫')
                    await message.add_reaction('🇦')
                    await message.add_reaction('🇳')
                    await message.add_reaction('🇮')
                    await message.add_reaction('🇲')
                    await message.add_reaction('🇪')
                elif rand == 2 or rand == 3:
                    path = random.choice(["assets/anime.png", "assets/yohjiman.jpg"])
                    with self.bot.storage.get(path) as file:
                        await message.channel.send(file=discord.File(file))
