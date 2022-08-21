from datetime import datetime

import discord
import pytz
from discord.ext import commands
from discord.utils import get


class AfterdarkCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_heartbeat(self) -> None:
        await self.process_afterdark()

    async def process_afterdark(self) -> None:
        for guild in self.bot.guilds:
            channel = get(guild.channels, name=self.bot.config['channels']['afterdark'])
            time = self.is_afterdark_time()
            if time and channel is None:
                print("afterdark time and channel does not exist")
                category = get(guild.channels, name='OFF TOPIC')
                active_role = get(guild.roles, name='active')
                bot_role = get(guild.roles, name='robot overlord')
                await guild.create_text_channel(
                    self.bot.config['channels']['afterdark'],
                    topic='temporary spicy late night chat (no porn)',
                    reason='afterdark time',
                    category=category,
                    overwrites={
                        guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        active_role: discord.PermissionOverwrite(read_messages=True),
                        bot_role: discord.PermissionOverwrite(read_messages=True),
                    },
                    nsfw=True
                )
            elif not time and channel is not None:
                print("past afterdark time and channel does exist")
                await channel.delete(reason='after afterdark')


    def is_afterdark_time(self) -> bool:
        zone = self.bot.config['time']['zone']
        tz = pytz.timezone(zone)
        hour = datetime.now(tz).hour
        return hour >= self.bot.config['time']['afterdark-start'] or hour <= self.bot.config['time']['afterdark-end']
