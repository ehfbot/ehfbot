import discord
from discord.ext import commands
from discord.utils import get
from discord_slash import SlashCommand, SlashContext

from .. import helper


class ActivityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.bot.add_slash_command(
            self.activity,
            name="activity",
            roles=['mod', 'admin'],
            channels=['bot'],
        )

class LurkersCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.bot.add_slash_command(
            self.purge,
            name="purge",
            roles=['mod', 'admin'],
            channels=['bot'],
        )

    async def purge(self, ctx: SlashContext) -> None:
        print(f"purging lurkers in server {ctx.guild.name}")
        users = list(filter(lambda member: self.lurker_detector(member), ctx.guild.members))
        print(f"found {len(users)} lurkers")
        await ctx.send(f"found {len(users)} lurkers")
        for user in users:
            print(f"kicking lurker {user.display_name}")
            await ctx.send(f"would be kicking lurker {user.display_name}")
            # await ctx.guild.kick(user=user, reason="lurker")
        await ctx.send(f"done")

    def lurker_detector(self, member):
        safe_roles = ['approved', 'legendary', 'bot']
        safe = next((role for role in safe_roles if get(member.roles, name=role) is not None), None)
        return not safe
