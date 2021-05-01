from typing import Callable, List

import discord
from discord.ext import commands

from .. import helper


class NoveltyCog(commands.Cog):
    def __new__(cls, bot=commands.Bot, *args, **kwargs):
        cls.create_link_commands(bot.config['commands']['links'])
        cls.create_image_commands(bot.config['commands']['images'])
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @classmethod
    def add_command_fn(cls, name: str, action: Callable[[commands.Context], None]) -> None:
        @commands.command(name=name, hidden=True)
        async def fn(self, ctx: commands.Context):
            print(name)
            await action(ctx)
        setattr(cls, name, fn)
        fn.__name__ = name
        cls.__cog_commands__.append(fn)

    @staticmethod
    def link_command(link: str) -> Callable:
        async def fn(ctx: commands.Context) -> None:
            await ctx.send(link)
        return fn

    @staticmethod
    def image_command(image: str) -> Callable:
        async def fn(ctx: commands.Context) -> None:
            with ctx.bot.storage.get(f"assets/{image}") as file:
                await ctx.send(file=discord.File(file))
        return fn

    @classmethod
    def create_link_commands(cls, links: list) -> None:
        if not len(links): return
        for cmd, link in links.items():
            cls.add_command_fn(cmd, cls.link_command(link))

    @classmethod
    def create_image_commands(cls, images: list) -> None:
        if not len(images): return
        for cmd, image in images.items():
            cls.add_command_fn(cmd, cls.image_command(image))

    @commands.command(hidden=True)
    async def buttmuscle(self, ctx: commands.Context) -> None:
        print('buttmuscle')
        path = "assets/buttmusclespicy.jpg" if ctx.channel.name == 'afterdark' else "assets/buttmuscle.jpg"
        with ctx.bot.storage.get(path) as file:
            await ctx.send(file=discord.File(file))
        await ctx.send(content='http://buttmuscle.eu/')

    @commands.command(hidden=True)
    async def katon(self, ctx: commands.Context) -> None:
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

    @commands.command(hidden=True)
    async def fakegeekgirls(self, ctx: commands.Context) -> None:
        print('fakegeekgirls')
        if not await self.bot.warn_meta_channel(ctx): return
        await ctx.send("https://discord.gg/agJ6vUD")

    @commands.command(hidden=True)
    async def bayareameetup(self, ctx: commands.Context) -> None:
        print('bayareameetup')
        if not await self.bot.warn_meta_channel(ctx): return
        await ctx.send("https://discord.gg/ySmcTZD")
