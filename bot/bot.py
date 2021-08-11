import asyncio
import os
import re
import sys
import tempfile
from collections import UserDict
from contextlib import contextmanager

import boto3
import discord
import yaml
from discord.ext import commands, tasks
from dotenv import dotenv_values

from bot import cogs, helper


class Env(UserDict):
    REQUIRED_KEYS = ('DISCORD_TOKEN', 'S3_REGION', 'S3_BUCKET', 'AWS_KEY', 'AWS_SECRET')

    def __init__(self):
        self.data = dotenv_values(".env") # only used in development
        for key in self.REQUIRED_KEYS:
            value = os.getenv(key) # used in heroku/production
            if value:
                self.data[key] = value

        self.warn_about_missing_keys()

    def warn_about_missing_keys(self):
        if set(self.REQUIRED_KEYS) - set(self.data):
            sys.exit(f"{self.REQUIRED_KEYS} must be set in environment")

class Storage(object):
    def __init__(self, env):
        self.session = boto3.resource(
            service_name='s3',
            region_name=env['S3_REGION'],
            aws_access_key_id=env['AWS_KEY'],
            aws_secret_access_key=env['AWS_SECRET']
        )
        self.bucket = self.session.Bucket(env['S3_BUCKET'])

    @contextmanager
    def get(self, path):
        filename, file_extension = os.path.splitext(path)
        temporary_file = tempfile.NamedTemporaryFile(suffix=file_extension)
        self.bucket.download_file(path, temporary_file.name)
        with open(temporary_file.name, 'rb') as file:
            try:
                yield file
            finally:
                temporary_file.close()

class Config(UserDict):
    def __init__(self, env):
        self.data = self.load_config()
        self.data.update(self.load_env(env))

    def load_config(self):
        data = {}
        with open('config/app.yml', 'r') as file:
            data = yaml.load(file.read(), Loader=yaml.FullLoader)
        return data

    def load_env(self, env):
        return ({
            'discord': {
                'token': env['DISCORD_TOKEN'],
            },
        })

class Bot(commands.Bot):
    @classmethod
    def create(cls):
        env = Env()
        storage = Storage(env=env)
        config = Config(env=env)
        self = Bot(env=env, storage=storage, config=config)
        return self

    def __init__(self, env, storage, config):
        self.env = env
        self.storage = storage
        self.config = config
        intents = discord.Intents.default()
        intents.members = True

        print(f"setting prefix to {self.config['commands']['prefix']}")
        super().__init__(command_prefix=self.config['commands']['prefix'], intents=intents)

        self.add_cog(cogs.PresenceCog(self))
        self.add_cog(cogs.WelcomeCog(self))
        self.add_cog(cogs.RolerCog(self))
        self.add_cog(cogs.AfterdarkCog(self))
        self.add_cog(cogs.RealtalkCog(self))
        self.add_cog(cogs.ActivityCog(self))
        self.add_cog(cogs.LurkersCog(self))
        self.add_cog(cogs.AnimeCog(self))
        self.add_cog(cogs.NoveltyCog(self))

        self.heartbeat_loop.start()

    def run(self) -> None:
        super().run(self.config['discord']['token'])

    def check_meta_channel(self, ctx: commands.Context) -> bool:
        return ctx.channel.name == self.config['channels']['meta']

    async def warn_meta_channel(self, ctx: commands.Context) -> bool:
        if not self.check_meta_channel(ctx):
            await ctx.send(f"take it to #{self.config['channels']['meta']}")
            return False
        return True

    def check_bot_channel(self, ctx: commands.Context) -> bool:
        return ctx.channel.name == self.config['channels']['bot']

    async def warn_bot_channel(self, ctx: commands.Context) -> bool:
        if not self.check_bot_channel(ctx):
            await ctx.send(f"take it to #{self.config['channels']['bot']}")
            return False
        return True

    # discord.py doesn't have on_heartbeat like discordrb
    @tasks.loop(seconds=10.0)
    async def heartbeat_loop(self) -> None:
        if not self.is_closed():
            self.dispatch('heartbeat')

    @heartbeat_loop.before_loop
    async def before_heartbeat_loop(self):
        print("waiting for bot to be ready")
        await self.wait_until_ready()
        print("bot is ready")

