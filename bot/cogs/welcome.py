import discord
from discord.ext import commands
from discord.utils import get


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        print('WelcomeCog on_member_join')
        guild = member.guild
        approved_role = get(guild.roles, name='approved')
        # display waiting room message
        if approved_role not in member.roles:
            await member.send(self.bot.config['commands']['waiting-pm'])
        else:
            await member.send(self.bot.config['commands']['welcome-pm'])
            await self._welcome_user(guild, member)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        member = after
        guild = member.guild
        approved_role = get(guild.roles, name='approved')
        timeout_role = get(guild.roles, name='timeout')
        if approved_role not in before.roles and approved_role in after.roles and timeout_role not in after.roles:
            print("approved a new user")
            await member.send(self.bot.config['commands']['welcome-pm'])
            await self._welcome_user(guild, member)


    async def _welcome_user(self, guild: discord.Guild, user: [discord.User, discord.Member]) -> None:
        channel = get(guild.channels, name=self.bot.config['channels']['welcome'])
        if channel is None: return
        await channel.send(f"everyone please welcome {user.mention}")
