import typing

import discord


def distinct(user: discord.User) -> str:
    return f"{user.name}#{user.discriminator}"

def lookup_roles(roles: typing.Sequence[discord.Role], names: typing.Sequence[str]) -> typing.Sequence[discord.Role]:
    lnames = list(map(lambda name: name.lower(), names))
    return list(filter(lambda role: role.name.lower() in lnames, roles))
