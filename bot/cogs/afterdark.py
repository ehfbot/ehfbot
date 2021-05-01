from datetime import datetime

import discord
import pytz
from discord.ext import commands

from .. import helper


class AfterdarkCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    @commands.Cog.listener()
    async def on_heartbeat(self) -> None:
        await self.process_afterdark()

    async def process_afterdark(self) -> None:
        #print("process_afterdark")
        for guild in self.bot.guilds:
            channel = helper.lookup_channel(guild.channels, self.bot.config['channels']['afterdark'])
            time = self.is_afterdark_time()
            if time and channel is None:
                print("afterdark time and channel does not exist")
                category = helper.lookup_channel(guild.channels, 'off topic')
                print(f"category: {category} {type(category)}")
                await guild.create_text_channel(
                    self.bot.config['channels']['afterdark'],
                    topic='temporary spicy late night chat. will be deleted. (no porn)',
                    reason='afterdark time',
                    category=category,
                    nsfw=True
                )
            elif not time and channel is not None:
                print("past afterdark time and channel does exist")
                await channel.delete(reason='after afterdark')


    def is_afterdark_time(self) -> bool:
        zone = self.bot.config['time']['zone']
        tz = pytz.timezone(zone)
        hour = datetime.now(tz).hour
        #print(f"the hour is {hour}")
        return hour >= self.bot.config['time']['afterdark-start'] or hour <= self.bot.config['time']['afterdark-end']
