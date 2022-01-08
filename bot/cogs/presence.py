import discord
from discord.ext import commands


class PresenceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.process_presence()

    async def process_presence(self) -> None:
        game = discord.Game(f"take it to #{self.bot.config['channels']['meta']}")
        await self.bot.change_presence(status=discord.Status.online, activity=game)
