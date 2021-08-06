from datetime import datetime, timedelta

import discord
from discord.ext import commands

from .. import helper


class RealtalkCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_heartbeat(self) -> None:
        await self.process_realtalk()

    async def process_realtalk(self) -> None:
        for channel in await self.find_channels():
            await self.purge_messages(channel)

    async def find_channels(self) -> list:
        channels = []

        for guild in self.bot.guilds:
            parent = helper.lookup_channel(channels=guild.channels, name=self.bot.config['channels']['realtalk'])
            if parent is None: continue

            channels.append(parent)

            threads = parent.threads
            if threads is None: continue

            for channel in threads:
                channels.append(channel)

        return channels

    async def purge_messages(self, channel) -> None:
        # must use utcnow as further down discord does a subtraction assuming a tz naive utc time
        before = datetime.utcnow() - timedelta(hours=self.bot.config['time']['realtalk-expiry'])
        # print(f"pruning #realtalk messages before {before} {channel.name}")
        try:
            await channel.purge(limit=10000, before=before, bulk=False)
        except (discord.errors.NotFound, discord.errors.Forbidden):
            pass
