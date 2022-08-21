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
            if channel is None:
                print("afterdark channel does not exist")
                category = get(guild.channels, name='OFF TOPIC')
                active_role = get(guild.roles, name='active')
                await guild.create_text_channel(
                    self.bot.config['channels']['afterdark'],
                    topic='temporary spicy late night chat (no porn)',
                    reason='afterdark time',
                    category=category,
                    overwrites={
                        guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        active_role: discord.PermissionOverwrite(read_messages=True),
                    },
                    nsfw=True
                )

            overwrite = channel.overwrites_for(guild.default_role)
            time = self.is_afterdark_time()
            if overwrite.view_channel == False and time:
                print("afterdark time and channel is not visible")
                await channel.set_permissions(guild.default_role, view_channel=True)
            elif overwrite.view_channel == False and not time:
                print("past afterdark time and channel is visible")
                await channel.set_permissions(guild.default_role, view_channel=False)

    def is_afterdark_time(self) -> bool:
        zone = self.bot.config['time']['zone']
        tz = pytz.timezone(zone)
        hour = datetime.now(tz).hour
        return hour >= self.bot.config['time']['afterdark-start'] or hour <= self.bot.config['time']['afterdark-end']
