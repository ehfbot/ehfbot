import asyncio
import logging
import os
import re
import sys
import tempfile
import typing
from collections import UserDict
from contextlib import contextmanager

import boto3
import discord
import discord_slash
import yaml
from discord.ext import commands, tasks
from discord_slash import SlashCommand, SlashContext
from dotenv import dotenv_values

from bot import cogs, helper

logging.basicConfig(level=logging.DEBUG)

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
        bot = Bot(env=env, storage=storage, config=config)
        return bot

    def __init__(self, env, storage, config):
        self.env = env
        self.storage = storage
        self.config = config
        intents = discord.Intents.default()
        intents.members = True

        # we are moving away from commands
        # but still want to support the main ones for a while
        print(f"setting prefix to {self.config['commands']['prefix']}")
        super().__init__(command_prefix=self.config['commands']['prefix'], intents=intents)

        # "global" interactions without explicit guild_ids
        # take hours to register
        self.guild_ids = None
        override_guild_ids = env['GUILD_IDS']
        if override_guild_ids is not None:
            self.guild_ids = list(map(int, override_guild_ids.split(',')))
            print(f"setting guild_ids to {self.guild_ids} for faster slash command registration")

        self.slash = SlashCommand(self, sync_commands=True, sync_on_cog_reload=True, override_type=True)
        self.add_slash_command(self.ping, name="ping")

        initial_cogs = [
            cogs.PresenceCog,
            cogs.WelcomeCog,
            cogs.RolerCog,
            cogs.AfterdarkCog,
            cogs.RealtalkCog,
            cogs.ActivityCog,
            cogs.LurkersCog,
            cogs.AnimeCog,
            cogs.NoveltyCog,
        ]
        for cog in initial_cogs:
            self.add_cog(cog(self))

        self.heartbeat_loop.start()

    def run(self) -> None:
        super().run(self.config['discord']['token'])

    def add_slash_command(
        self,
        cmd: typing.Callable,
        roles: typing.Optional[typing.Sequence] = None,
        channels: typing.Optional[typing.Sequence] = None,
        options: typing.Optional[typing.Sequence] = None,
        **kwargs
    ) -> None:
        async def wrapper(ctx: SlashContext, cmd=cmd, **kwargs):
            return await cmd(ctx, **kwargs)

        def check_channels(channels: typing.Sequence):
            def predicate(ctx: SlashContext):
                print(f"channels: {channels}")
                if channels is None: return True
                for channel in channels:
                    name = self.config['channels'].get(channel, channel)
                    if ctx.channel.name == name:
                        return True
                return False
            return commands.check(predicate)

        cmd = check_channels(channels)(wrapper)

        if roles is not None:
            cmd = commands.has_any_role(*roles)(cmd)

        # have to set a dummy list to prevent
        # discord_slash from probing our cmd's args
        if options is None:
            options = []

        return self.slash.add_slash_command(
            cmd,
            guild_ids=self.guild_ids,
            options=options,
            **kwargs
        )

    # on a regular interval we will dispatch a heartbeat to cogs
    @tasks.loop(seconds=10.0)
    async def heartbeat_loop(self) -> None:
        if not self.is_closed():
            self.dispatch('heartbeat')

    @heartbeat_loop.before_loop
    async def before_heartbeat_loop(self):
        print("waiting for bot to be ready")
        await self.wait_until_ready()
        print("bot is ready")

    async def on_ready(self):
        print("on_ready")

    async def on_slash_command_error(self, ctx, ex):
        print('on_slash_command_error')
        if isinstance(ex, discord.ext.commands.errors.MissingAnyRole):
            await ctx.send("Permission check failed", hidden=True)
        elif isinstance(ex, discord_slash.error.CheckFailure):
            await ctx.send("Channel check failed", hidden=True)
        else:
            await ctx.send('Oopsie woopsie', hidden=True)
            print(ex)
            # raise ex

    async def ping(self, ctx: SlashContext) -> None:
        print("ping")
        await ctx.send(content='pong')
