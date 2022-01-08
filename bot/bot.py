import typing

import discord
import discord_slash
from discord.ext import commands, tasks
from discord_slash import SlashCommand, SlashContext

from bot import cogs, entities, helper
from bot.config import config
from bot.db import db
from bot.env import env
from bot.storage import storage


class Bot(commands.Bot):
    @classmethod
    def create(cls):
        bot = Bot(env=env, storage=storage, config=config, db=db)
        # bot = Bot(env=env.env, storage=storage.storage, config=config.config, db=db.db)
        return bot

    def __init__(self, env, storage, config, db):
        self.env = env
        self.storage = storage
        self.config = config
        self.db = db
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
            cogs.PostingCog,
            cogs.WelcomeCog,
            cogs.RolerCog,
            cogs.AfterdarkCog,
            cogs.RealtalkCog,
            cogs.ActivityCog,
            cogs.LurkersCog,
            cogs.AnimeCog,
            cogs.NoveltyCog,
            cogs.AnnoyingCog,
        ]
        for cog in initial_cogs:
            self.add_cog(cog(self))

        # set the db up
        self.db.generate_mapping(create_tables=False)

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
            await ctx.channel.send("Permission check failed")
        elif isinstance(ex, discord_slash.error.CheckFailure):
            await ctx.channel.send("Channel check failed")
        else:
            await ctx.channel.send('Oopsie woopsie')
            print(ex)
            # raise ex

    async def ping(self, ctx: SlashContext) -> None:
        print("ping")
        await ctx.send(content='pong')

bot = Bot.create()
