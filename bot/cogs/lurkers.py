import discord
from discord.ext import commands

from .. import helper


class LurkersCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def purge(self, ctx: commands.Context) -> None:
        if not await self.bot.warn_bot_channel(ctx): return
        print(f"purging lurkers in server {ctx.guild.name}")
        users = list(filter(lambda member: helper.lookup_role(member.roles, 'approved') is not None, ctx.guild.members))
        print(f"found {len(users)} lurkers")
        await ctx.send(f"found {len(users)} lurkers")
        for user in users:
            ctx.guild.kick(user=user, reason="lurker")

