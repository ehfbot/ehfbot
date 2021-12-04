import re
from typing import Callable, List

import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext

from .. import helper


class NoveltyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

        self.bot.add_slash_command(
            self.buttmuscle,
            name="buttmuscle",
        )

        self.bot.add_slash_command(
            self.katon,
            name="katon",
        )

        for name, link in bot.config.get('commands', {}).get('links', {}).items():
            cmd = lambda link: lambda ctx: ctx.send(link)
            self.bot.add_slash_command(cmd(link), name=name)

        for name, image in bot.config.get('commands', {}).get('images', {}).items():
            cmd = lambda image: lambda ctx: self._send_file_wrapper(ctx=ctx, image=image)
            self.bot.add_slash_command(cmd(image), name=name)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        await self._reaction_phrases(message)
        await self._ping_images(message)

    async def _reaction_phrases(self, message: discord.Message) -> None:
        if re.match(r'^(ad,?ao|anoth(a|er) ?day ?,? ?anoth(a|er) ?opp).*$', message.content.lower()):
            await message.add_reaction('💯')
            return

    async def _ping_images(self, message: discord.Message) -> None:
        roles_pinged = list(map(lambda role: role.name, message.role_mentions))
        for role, image in self.bot.config.get('pings', {}).get('images', {}).items():
            if role in roles_pinged:
                with self.bot.storage.get(f"assets/{image}") as file:
                    await message.channel.send(file=discord.File(file))

    # wrapper to be able to lambda this in a one-liner
    async def _send_file_wrapper(self, ctx: SlashContext, image: str) -> None:
        with ctx.bot.storage.get(f"assets/{image}") as file:
            await ctx.send(file=discord.File(file))

    async def buttmuscle(self, ctx: SlashContext) -> None:
        print('buttmuscle')
        path = "assets/buttmusclespicy.jpg" if ctx.channel.name == 'afterdark' else "assets/buttmuscle.jpg"
        with ctx.bot.storage.get(path) as file:
            await ctx.send(file=discord.File(file))
        await ctx.send(content='http://buttmuscle.eu/')

    async def katon(self, ctx: SlashContext) -> None:
        print('katon')
        user_distinct = helper.distinct(ctx.author)
        if user_distinct == 'Katon#6969':
            path = "assets/katonkaton.png"
        elif user_distinct == 'brissings#4367':
            path = "assets/katonbrissings.png"
        else:
            path = "assets/katon.png"
        with ctx.bot.storage.get(path) as file:
            await ctx.send(file=discord.File(file))
