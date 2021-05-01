import asyncio
from datetime import datetime
from typing import List

import discord
from discord.ext import commands

from . import helper


class Pruner():
    def __init__(self, channel: discord.TextChannel, before: datetime = None):
        self.channel = channel
        self.before = before
        self.stop = False

    async def prune(self) -> None:
        print(f'pruner pruning {self.channel}')
        async for message in self.channel.history(limit=100, before=self.before):
            print(message)
            await self.delete_message(message)
            print('done deleting that message')
            if self.stop: break
            # await asyncio.sleep(10)
        pass

    def stop(self) -> None:
        self.stop = True

    async def delete_message(self, message: discord.Message) -> None:
        if self.check_message(message): await message.delete()

    def check_message(self, message: discord.Message) -> bool:
        print(f"message.created_at: {message.created_at}")
        print(f"self.before: {self.before}")
        return not self.before or message.created_at < self.before
