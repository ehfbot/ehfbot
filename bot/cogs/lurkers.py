import discord
from discord.ext import commands
from discord.utils import get
from discord_slash import SlashCommand, SlashContext


class LurkersCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # permission check needed for slash conversion
    async def purge(self, ctx: SlashContext) -> None:
        print(f"purging lurkers in server {ctx.guild.name}")
        users = list(filter(lambda member: get(member.roles, name='approved') is not None, ctx.guild.members))
        print(f"found {len(users)} lurkers")
        await ctx.send(f"found {len(users)} lurkers")
