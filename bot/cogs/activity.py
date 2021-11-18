import re
from datetime import datetime, timedelta
from typing import TypedDict

import discord
from discord.ext import commands
from discord.utils import get
from discord_slash import SlashCommand, SlashContext

from .. import helper


class UserCounts(TypedDict):
    messages: int
    adjusted: int
    words: int
    days: dict[str, bool]


class ActivityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.bot.add_slash_command(
            self.activity,
            name="activity",
            roles=['mod', 'admin'],
            channels=['bot'],
        )

    async def activity(self, ctx: SlashContext) -> None:
        role = get(ctx.guild.roles, name='active')
        if not role:
            await ctx.send("no active role")
            return

        await ctx.send("tallying post counts")
        counts = await self.process_postcounts(ctx.guild)
        count_sorted = sorted(counts.items(), key=lambda v:v[1]['adjusted'], reverse=True)
        for id, count in count_sorted:
            member = ctx.guild.get_member(id)
            if not member: continue
            await ctx.send(f"{member.display_name}: {count['adjusted']} / {count['messages']} messages with {count['words']} words over {len(count['days'])} days")
            is_active = get(member.roles, name='active') is not None

            if count['adjusted'] >= self.bot.config['activity']['messages'] and len(count['days']) >= self.bot.config['activity']['days']:
                if is_active:
                    await ctx.send("already in active")
                    continue
                await ctx.send("adding to active")
                await member.add_roles(role)
            else:
                if not is_active:
                    await ctx.send("not in active")
                    continue
                await ctx.send("removing from active")
                await member.remove_roles(role)

        # remove rest of inactive lurkers not in count list
        counted_ids = counts.keys()
        lurkers = list(filter(lambda member: member.id not in counted_ids, ctx.guild.members))
        await ctx.send(f"found {len(lurkers)} lurkers")
        for member in lurkers:
            await ctx.send(f"{member.display_name}: lurker")
            try:
                await member.edit(roles=[])
            except discord.errors.Forbidden:
                print("access denied removing roles")
                pass

        await ctx.send("EHF LEADERBOARDS")
        count_sorted = sorted(counts.items(), key=lambda v:v[1]['messages'], reverse=True)
        for id, count in count_sorted[0:10]:
            member = ctx.guild.get_member(id)
            if not member: continue
            await ctx.send(f"@{helper.distinct(member)}: {count['messages']} messages ({count['adjusted']})")

    async def process_postcounts(self, guild: discord.Guild) -> dict[str, UserCounts]:
        window = datetime.now() - timedelta(days=self.bot.config['activity']['window'])
        users = {}
        print(f"processing postcounts in server {guild.name}")
        for channel in guild.channels:
            if type(channel) != discord.TextChannel: continue
            if channel.name == self.bot.config['channels']['realtalk']: continue
            if channel.name == self.bot.config['channels']['bot']: continue
            print(f"processing postcounts in channel #{channel.name}")
            last_id = None
            last_user = None
            count = 0
            try:
                async for message in channel.history(limit=100000, after=window):
                    count += 1
                    users.setdefault(message.author.id, {'messages': 0, 'adjusted': 0, 'words': 0, 'days': {}})
                    users[message.author.id]['messages'] += 1
                    users[message.author.id]['words'] += len(re.split("\s+", message.content))
                    if len(message.content) >= 10:
                        users[message.author.id]['days'][message.created_at.strftime('%Y-%m-%d')] = True
                        if last_user is not message.author.id: users[message.author.id]['adjusted'] += 1
                        last_user = message.author.id
            except discord.errors.Forbidden:
                print("access denied")
                pass
            print(f"got {count} messages")
        return users
