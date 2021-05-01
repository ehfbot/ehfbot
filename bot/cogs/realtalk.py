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
        for guild in self.bot.guilds:
            channel = helper.lookup_channel(guild.channels, self.bot.config['channels']['realtalk'])
            if channel is None: continue

            # must use utcnow as further down discord does a subtraction assuming a tz naive utc time
            before = datetime.utcnow() - timedelta(hours = self.bot.config['time']['realtalk-expiry'])
            #print(f"pruning #realtalk messages before {before} {channel}")
            try:
                result = await channel.purge(limit=10000, before=before, bulk=False)
                #print(f"done pruning #realtalk {result}")
            except discord.errors.NotFound:
                pass

            # history = await channel.history(before=before).flatten()
            # print(f"history {len(history)}")
