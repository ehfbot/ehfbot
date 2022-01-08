import itertools
import re
import typing
from collections import UserDict

import discord
from discord.ext import commands
from discord.utils import get
from discord_slash import SlashContext, cog_ext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option

from .. import helper


class RolerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.bot.add_slash_command(
            self.whomst,
            name="whomst",
            channels=['meta'],
            options=[
                create_option(
                    name="mentionable",
                    description="member or role",
                    option_type=SlashCommandOptionType.MENTIONABLE,
                    required=True,
                ),
            ]
        )

        self.bot.add_slash_command(
            self.roles,
            name="roles",
        )

        self.bot.add_slash_command(
            self.addroles,
            name="addroles",
            channels=['meta'],
            options=[
                create_option(
                    name="roles",
                    description="roles list",
                    option_type=SlashCommandOptionType.STRING,
                    required=False,
                ),
            ]
        )
        self.bot.add_slash_command(
            self.addrole,
            name="addrole",
            channels=['meta'],
            options=[
                create_option(
                    name="role",
                    description="role name",
                    option_type=SlashCommandOptionType.ROLE,
                    required=True,
                ),
            ]
        )

        self.bot.add_slash_command(
            self.removeroles,
            name="removeroles",
            channels=['meta'],
            options=[
                create_option(
                    name="roles",
                    description="roles list",
                    option_type=SlashCommandOptionType.STRING,
                    required=False,
                ),
            ]
        )
        self.bot.add_slash_command(
            self.removerole,
            name="removerole",
            channels=['meta'],
            options=[
                create_option(
                    name="role",
                    description="role name",
                    option_type=SlashCommandOptionType.ROLE,
                    required=True,
                ),
            ]
        )

    async def whomst(self, ctx: typing.Union[commands.Context, SlashContext], mentionable: typing.Optional[str] = None) -> None:
        print('whomst')
        if not mentionable:
            await ctx.send("whomst is whomst?")
            return

        role = get(ctx.guild.roles, id=int(mentionable))
        if role:
            await self.whoisin(ctx, role=role)

        member = get(ctx.guild.members, id=int(mentionable))
        if member:
            await self.whois(ctx, member=member)

        if not role and not member:
            await ctx.send('nobody')

    async def whoisin(self, ctx: typing.Union[commands.Context, SlashContext], role: discord.Role = None) -> None:
        print('whoisin')
        if not role:
            await ctx.send("whomst wheremst?")
            return

        if role.name == 'active':
            await ctx.send('algorithmically determined active users')
            return
        if not role.members:
            await ctx.send('nobody')
            return

        names = list(map(lambda member: re.sub(r'([`|])', r'\\\1', member.display_name), role.members))
        await ctx.send(', '.join(names))

    async def whois(self, ctx: typing.Union[commands.Context, SlashContext], member: discord.Member = None) -> None:
        print('whois')
        if not member:
            await ctx.send("whomst whomst?")
            return

        embed = discord.Embed(title=helper.distinct(member)) \
            .set_image(url=member.avatar.url) \
            .add_field(name='registered', value=member.created_at.strftime('%Y-%m-%d')) \
            .add_field(name='joined', value=member.joined_at.strftime('%Y-%m-%d')) \
            .add_field(name='roles', inline=False, value=' '.join(map(lambda role: role.name, member.roles)))

        await ctx.send(embed=embed)

    async def roles(self, ctx: typing.Union[commands.Context, SlashContext]) -> None:
        await Roler(ctx).list_roles()

    async def addroles(self, ctx: typing.Union[commands.Context, SlashContext], roles: str) -> None:
        await Roler(ctx).add_roles(roles)

    async def addrole(self, ctx: typing.Union[commands.Context, SlashContext], role: discord.abc.Role) -> None:
        await self.addroles(ctx, role.name)

    async def removeroles(self, ctx: typing.Union[commands.Context, SlashContext], roles: str) -> None:
        await Roler(ctx).remove_roles(roles)

    async def removerole(self, ctx: typing.Union[commands.Context, SlashContext], role: discord.abc.Role) -> None:
        await self.removeroles(ctx, role.name)


class Roler():
    def __init__(self, ctx: typing.Union[commands.Context, SlashContext]):
        self.ctx = ctx

    async def list_roles(self) -> None:
        config_roles = self.config_roles()
        if not config_roles:
            await self.ctx.send('no roles defined')
            return
        for key, roles in config_roles.items():
            await self.ctx.send(f"{key}: {', '.join(roles)}")

    async def add_roles(self, roles: str) -> None:
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

    async def remove_roles(self, roles: str) -> None:
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
        return get(self.ctx.author.roles, name='approved') is not None

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
    def __init__(self, data: str) -> list:
        data = data.split(' ')
        data = map(lambda role: role.split(','), data)
        data = itertools.chain.from_iterable(data)
        data = map(lambda role: re.sub(r'[\s,@]', '', role), data)
        data = map(lambda role: role.lower(), data)
        self.data = list(filter(None, data))
