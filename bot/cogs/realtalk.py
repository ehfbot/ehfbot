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

            threads = helper.lookup_threads(channels=guild.channels, parent=parent)
            if threads is None:
                print(f"found zero #realtalk threads")
                print(f"realtalk channel id #{parent.id}")
                all_threads = list(map(lambda channel: channel, guild.channels))
                all_threads = list(filter(lambda channel: hasattr(channel, 'parent_id'), roles))
                print(f"found #{len(all_threads)} total threads")
                if all_threads is not None and len(all_threads) > 0:
                    print(f"first thread parent_id #{all_threads[0].parent_id}")

                continue

            print(f"found #{len(threads)} #realtalk threads")

            for channel in threads:
                channels.append(channel)

        return channels

    async def purge_messages(self, channel) -> None:
        # must use utcnow as further down discord does a subtraction assuming a tz naive utc time
        before = datetime.utcnow() - timedelta(hours=self.bot.config['time']['realtalk-expiry'])
        print(f"pruning #realtalk messages before {before} {channel.name}")
        try:
            await channel.purge(limit=10000, before=before, bulk=False)
        except discord.errors.NotFound:
            pass
