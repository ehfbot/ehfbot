from typing import List

import discord


def distinct(user: discord.User) -> str:
    return f"{user.name}#{user.discriminator}"

def lookup_role(roles: List[discord.Role], name: str) -> [discord.Role, None]:
    return next((role for role in roles if role.name.lower() == name.lower()), None)

def lookup_roles(roles: List[discord.Role], names: List[str]) -> List[discord.Role]:
    lnames = list(map(lambda name: name.lower(), names))
    return list(filter(lambda role: role.name.lower() in lnames, roles))

def lookup_channel(channels: List[discord.abc.GuildChannel], name: str) -> [discord.abc.GuildChannel, None]:
    return next((channel for channel in channels if channel.name.lower() == name.lower()), None)

def lookup_member(members: List[discord.Member], name: str) -> [discord.Member, None]:
    lname = name.lower()
    return next((member for member in members if member.name.lower() == lname or member.display_name.lower() == lname), None)