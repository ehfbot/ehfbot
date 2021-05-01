import itertools
import re
from collections import UserDict

import discord
from discord.ext import commands

from .. import helper


class RolerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def whomst(self, ctx: commands.Context, *name) -> None:
        print('whomst')
        name = ' '.join(name)
        if not await self.bot.warn_meta_channel(ctx): return
        if not name:
            await ctx.send("whomst is whomst?")
            return

        role = helper.lookup_role(ctx.guild.roles, name)
        if role:
            await ctx.invoke(self.bot.get_command('whoisin'), name)

        user = helper.lookup_member(ctx.guild.members, name)
        if user:
            await ctx.invoke(self.bot.get_command('whois'), name)

        if not role and not user:
            await ctx.send('nobody')

    @commands.command(hidden=True)
    async def whois(self, ctx: commands.Context, *name) -> None:
        print('whois')
        name = ' '.join(name)
        if not await self.bot.warn_meta_channel(ctx): return
        if not name:
            await ctx.send("whois whomst?")
            return

        member = helper.lookup_member(ctx.guild.members, name)
        if not member:
            await ctx.send("nobody")
            return

        embed = discord.Embed(title=helper.distinct(member)) \
            .set_image(url=member.avatar_url) \
            .add_field(name='registered', value=member.created_at.strftime('%Y-%m-%d')) \
            .add_field(name='joined', value=member.joined_at.strftime('%Y-%m-%d')) \
            .add_field(name='roles', inline=False, value=' '.join(map(lambda role: role.name, member.roles)))

        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def whoisin(self, ctx: commands.Context, *name) -> None:
        print('whoisin')
        if not await self.bot.warn_meta_channel(ctx): return
        name = ' '.join(name)
        if not name:
            await ctx.send("whoisin wheremst?")
            return

        role = helper.lookup_role(ctx.guild.roles, name)
        if not role:
            await ctx.send("#{name} does not exist")
            return
        if role.name == 'active':
            await ctx.send('algorithmically determined active users')
            return
        if not role.members:
            await ctx.send('nobody')
            return
        names = list(map(lambda member: re.sub(r'([`|])', r'\\\1', member.display_name), role.members))
        await ctx.send(', '.join(names))

    @commands.command()
    async def roles(self, ctx: commands.Context) -> None:
        await Roler(ctx).list_roles()

    @commands.command()
    async def addroles(self, ctx: commands.Context, *roles: str) -> None:
        print(f'addroles {roles}')
        if not await self.bot.warn_meta_channel(ctx): return
        cmds = ['fakegeekgirls', 'bayareameetup', 'doge']
        for cmd in list(set(roles) & set(cmds)):
            print(cmd)
            await ctx.invoke(self.bot.get_command(cmd))

        await Roler(ctx).add_roles((set(roles) - set(cmds)))

    @commands.command(hidden=True)
    async def addrole(self, ctx: commands.Context, *roles: str) -> None:
        await ctx.invoke(self.bot.get_command('addroles'), *roles)

    @commands.command()
    async def removeroles(self, ctx: commands.Context, *roles: str) -> None:
        print('removeroles')
        if not await self.bot.warn_meta_channel(ctx): return
        await Roler(ctx).remove_roles(roles)

    @commands.command(hidden=True)
    async def removerole(self, ctx: commands.Context, *roles: str) -> None:
        await ctx.invoke(self.bot.get_command('removeroles'), *roles)


class Roler():
    def __init__(self, ctx: commands.Context):
        self.ctx = ctx

    async def list_roles(self) -> None:
        config_roles = self.config_roles()
        if not config_roles:
            await self.ctx.send('no roles defined')
            return
        for key, roles in config_roles.items():
            await self.ctx.send(f"{key}: {', '.join(roles)}")

    async def add_roles(self, roles: list) -> None:
        if not self.check_user_approved: return
        if not self.check_config_roles_defined: return

        roles = RolesList(roles)
        flat_config_roles = self.flat_config_roles()
        valid = set(roles) & set(flat_config_roles)
        invalid = set(roles) - set(flat_config_roles)

        if not self.check_bannable(invalid):
            await self.ctx.send(f"you have been banned")
            return

        if valid:
            await self.ctx.send(f"adding to {', '.join(valid)}")
            svalid = helper.lookup_roles(self.ctx.guild.roles, valid)
            print(f"svalid: {svalid}")
            if svalid: await self.ctx.author.add_roles(*svalid)
        if invalid:
            await self.ctx.send(f"not adding to {', '.join(invalid)}")

    async def remove_roles(self, roles: list) -> None:
        if not self.check_user_approved: return
        if not self.check_config_roles_defined: return

        roles = RolesList(roles)
        flat_config_roles = self.flat_config_roles()
        valid = set(roles) & set(flat_config_roles)
        invalid = set(roles) - set(flat_config_roles)

        if not self.check_bannable(invalid):
            await self.ctx.send(f"you have been banned")
            return

        if valid:
            await self.ctx.send(f"removing from {', '.join(valid)}")
            svalid = helper.lookup_roles(self.ctx.guild.roles, valid)
            print(f"svalid: {svalid}")
            if svalid: await self.ctx.author.remove_roles(*svalid)
        if invalid:
            await self.ctx.send(f"not removing from {', '.join(invalid)}")

    def check_user_approved(self) -> bool:
        return self.ctx.bot.helper.lookup_role(self.ctx.author.roles, 'approved') is not None

    def check_config_roles_defined(self) -> bool:
        return self.ctx.bot.config['roles'] is not None

    def config_roles(self) -> list:
        return self.ctx.bot.config['roles']

    def check_bannable(self, invalid) -> bool:
        return not any(role in self.bannable_roles() for role in invalid)

    def flat_config_roles(self) -> list:
        roles = self.ctx.bot.config['roles'].values()
        roles = list(itertools.chain.from_iterable(roles))
        roles = list(map(lambda role: role.lower(), roles))
        return roles

    def bannable_roles(self) -> list:
        return ['mod', 'blackname', 'dad', 'fuzz', 'admin', 'bot', 'approved', 'losers', 'illuminatus', 'anime', 'weeb', 'weebs']

class RolesList(UserDict):
    def __init__(self, data):
        data = map(lambda role: role.split(','), data)
        data = itertools.chain.from_iterable(data)
        data = map(lambda role: re.sub(r'[\s,@]', '', role), data)
        data = map(lambda role: role.lower(), data)
        self.data = list(data)

