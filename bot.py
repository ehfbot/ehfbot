import asyncio
import inspect
import os
import random
import re
import itertools
from collections import UserDict
from datetime import datetime, timedelta
from typing import Callable, List
import pytz
import discord
import yaml
from discord.ext import commands

os.environ.setdefault('BOT_ENV', 'development')

class Config(UserDict):
    @classmethod
    def env(cls) -> str:
      return os.environ['BOT_ENV']

    def __init__(self, path: str):
        self.path = path
        data = {}
        try:
            with open(self.path, 'r') as f:
                data = yaml.full_load(f)
        except IOError:
            print('IOError')
            data = {}

        if Config.env() in data:
            data.update(data[Config.env()])
        self.data = data

def lookup_role(roles: List[discord.Role], name: str) -> [discord.Role, None]:
    return next((role for role in roles if role.name.lower() == name.lower()), None)

def lookup_roles(roles: List[discord.Role], names: List[str]) -> List[discord.Role]:
    lnames = list(map(lambda name: name.lower(), names))
    return list(filter(lambda role: role.name.lower() in lnames, roles))

def lookup_channel(channels: List[discord.abc.GuildChannel], name: str) -> [discord.abc.GuildChannel, None]:
    return next((channel for channel in channels if channel.name.lower() == name.lower()), None)

def lookup_member(members: List[discord.Member], name: str) -> [discord.Member, None]:
    lname = name.lower()
    return next((member for member in members if member.name.lower() == lname or member.display_name.lower() == lname), None)

def distinct(user: discord.User) -> str:
    return f"{user.name}#{user.discriminator}"

class EhfBot(commands.Bot):
    def __init__(self, config):
        self.config = config
        intents = discord.Intents.default()
        intents.members = True
        print(f"setting prefix to {self.config['commands']['prefix']}")
        super().__init__(command_prefix=self.config['commands']['prefix'], intents=intents)

        self.add_cog(self.PresenceCog(self))
        self.add_cog(self.WelcomeCog(self))
        self.add_cog(self.RolerCog(self))
        self.add_cog(self.AfterdarkCog(self))
        self.add_cog(self.RealtalkCog(self))
        self.add_cog(self.ActivityCog(self))
        self.add_cog(self.LurkersCog(self))
        self.add_cog(self.AnimeCog(self))
        self.add_cog(self.AnnoyingCog(self))
        self.add_cog(self.NoveltyCog(self))

        self.new_members = {}
        self.heartbeat_task = self.loop.create_task(self.heartbeat_loop())

    def run(self) -> None:
        super().run(self.config['discord']['token'])

    def check_meta_channel(self, ctx: commands.Context) -> bool:
        return ctx.channel.name == self.config['channels']['meta']

    async def warn_meta_channel(self, ctx: commands.Context) -> bool:
        if not self.check_meta_channel(ctx):
            await ctx.send(f"take it to #{self.config['channels']['meta']}")
            return False
        return True

    def check_bot_channel(self, ctx: commands.Context) -> bool:
        return ctx.channel.name == self.config['channels']['bot']

    async def warn_bot_channel(self, ctx: commands.Context) -> bool:
        if not self.check_bot_channel(ctx):
            await ctx.send(f"take it to #{self.config['channels']['bot']}")
            return False
        return True

    # discord.py doesn't have on_heartbeat like discordrb
    async def heartbeat_loop(self) -> None:
        await self.wait_until_ready()
        while not self.is_closed():
            self.dispatch('heartbeat')
            await asyncio.sleep(10)

    class PresenceCog(commands.Cog):
        def __init__(self, bot: commands.Bot):
            self.bot = bot

        @commands.Cog.listener()
        async def on_ready(self) -> None:
            await self.process_presence()

        async def process_presence(self) -> None:
            game = discord.Game(f"{self.bot.command_prefix}help for commands")
            await self.bot.change_presence(status=discord.Status.online, activity=game)

    class WelcomeCog(commands.Cog):
        def __init__(self, bot: commands.Bot):
            self.bot = bot

        @commands.Cog.listener()
        async def on_member_join(self, member: discord.Member) -> None:
            print('WelcomeCog on_member_join')
            guild = member.guild
            approved_role = lookup_role(guild.roles, 'approved')
            # display waiting room message
            if approved_role not in member.roles:
                await member.send(self.bot.config['commands']['waiting-pm'])
            else:
                await member.send(self.bot.config['commands']['welcome-pm'])
                await self.welcome_user(guild, member)

        @commands.Cog.listener()
        async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
            member = after
            guild = member.guild
            approved_role = lookup_role(guild.roles, 'approved')
            timeout_role = lookup_role(guild.roles, 'timeout')
            if approved_role not in before.roles and approved_role in after.roles and timeout_role not in after.roles:
                print("approved a new user")
                await member.send(self.bot.config['commands']['welcome-pm'])
                await self.welcome_user(guild, member)


        async def welcome_user(self, guild: discord.Guild, user: [discord.User, discord.Member]) -> None:
            channel = lookup_channel(guild.channels, self.bot.config['channels']['welcome'])
            if channel is None: return
            await channel.send(f"everyone please welcome {user.mention}")

    class RolerCog(commands.Cog):
        def __init__(self, bot: commands.Bot):
            self.bot = bot

        @commands.command()
        async def whomst(self, ctx: commands.Context, *name) -> None:
            print('whomst')
            name = ' '.join(name)
            if not await self.bot.warn_meta_channel(ctx): return
            if not name:
                await ctx.send("whomst is whomst?")
                return

            role = lookup_role(ctx.guild.roles, name)
            if role:
                await ctx.invoke(self.bot.get_command('whoisin'), name)

            user = lookup_member(ctx.guild.members, name)
            if user:
                await ctx.invoke(self.bot.get_command('whois'), name)

            if not role and not user:
                await ctx.send('nobody')

        @commands.command(hidden=True)
        async def whois(self, ctx: commands.Context, *name) -> None:
            print('whois')
            name = ' '.join(name)
            if not await self.bot.warn_meta_channel(ctx): return
            if not name:
                await ctx.send("whois whomst?")
                return

            member = lookup_member(ctx.guild.members, name)
            if not member:
                await ctx.send("nobody")
                return

            embed = discord.Embed(title=distinct(member)) \
                .set_image(url=member.avatar_url) \
                .add_field(name='registered', value=member.created_at.strftime('%Y-%m-%d')) \
                .add_field(name='joined', value=member.joined_at.strftime('%Y-%m-%d')) \
                .add_field(name='roles', inline=False, value=' '.join(map(lambda role: role.name, member.roles)))

            await ctx.send(embed=embed)

        @commands.command(hidden=True)
        async def whoisin(self, ctx: commands.Context, *name) -> None:
            print('whoisin')
            if not await self.bot.warn_meta_channel(ctx): return
            name = ' '.join(name)
            if not name:
                await ctx.send("whoisin wheremst?")
                return

            role = lookup_role(ctx.guild.roles, name)
            if not role:
                await ctx.send("#{name} does not exist")
                return
            if role.name == 'active':
                await ctx.send('algorithmically determined active users')
                return
            if not role.members:
                await ctx.send('nobody')
                return
            names = list(map(lambda member: re.sub(r'([`|])', r'\\\1', member.display_name), role.members))
            await ctx.send(', '.join(names))

        @commands.command()
        async def roles(self, ctx: commands.Context) -> None:
            await Roler(ctx).list_roles()

        @commands.command()
        async def addroles(self, ctx: commands.Context, *roles: str) -> None:
            print(f'addroles {roles}')
            if not await self.bot.warn_meta_channel(ctx): return
            cmds = ['fakegeekgirls', 'bayareameetup', 'doge']
            for cmd in list(set(roles) & set(cmds)):
                print(cmd)
                await ctx.invoke(self.bot.get_command(cmd))

            await Roler(ctx).add_roles((set(roles) - set(cmds)))

        @commands.command(hidden=True)
        async def addrole(self, ctx: commands.Context, *roles: str) -> None:
            await ctx.invoke(self.bot.get_command('addroles'), *roles)

        @commands.command()
        async def removeroles(self, ctx: commands.Context, *roles: str) -> None:
            print('removeroles')
            if not await self.bot.warn_meta_channel(ctx): return
            await Roler(ctx).remove_roles(roles)

        @commands.command(hidden=True)
        async def removerole(self, ctx: commands.Context, *roles: str) -> None:
            await ctx.invoke(self.bot.get_command('removeroles'), *roles)

    class AfterdarkCog(commands.Cog):
        def __init__(self, bot: commands.Bot):
            self.bot = bot

        @commands.Cog.listener()
        async def on_heartbeat(self) -> None:
            await self.process_afterdark()

        async def process_afterdark(self) -> None:
            #print("process_afterdark")
            for guild in self.bot.guilds:
                channel = lookup_channel(guild.channels, self.bot.config['channels']['afterdark'])
                time = self.is_afterdark_time()
                if time and channel is None:
                    print("afterdark time and channel does not exist")
                    category = lookup_channel(guild.channels, 'off topic')
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

    class RealtalkCog(commands.Cog):
        def __init__(self, bot: commands.Bot):
            self.bot = bot

        @commands.Cog.listener()
        async def on_heartbeat(self) -> None:
            await self.process_realtalk()

        async def process_realtalk(self) -> None:
            for guild in self.bot.guilds:
                channel = lookup_channel(guild.channels, self.bot.config['channels']['realtalk'])
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


    class ActivityCog(commands.Cog):
        def __init__(self, bot: commands.Bot):
            self.bot = bot

        @commands.command(hidden=True)
        async def activity(self, ctx: commands.Context) -> None:
            if not await self.bot.warn_bot_channel(ctx): return
            role = lookup_role(ctx.guild.roles, 'active')
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
                is_active = lookup_role(member.roles, 'active') is not None

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
                #is_active = lookup_role(member.roles, 'active') is not None
                await ctx.send(f"{member.display_name}: lurker")
                #if not is_active:
                    #await ctx.send("not in active")
                    #continue
                #await ctx.send("removing from active")
                #await member.remove_roles(role)
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
                await ctx.send(f"@{distinct(member)}: {count['messages']} messages ({count['adjusted']})")

        async def process_postcounts(self, guild: discord.Guild) -> set:
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
                        count+=1
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

    class LurkersCog(commands.Cog):
        def __init__(self, bot: commands.Bot):
            self.bot = bot

        @commands.command(hidden=True)
        async def purge(self, ctx: commands.Context) -> None:
            if not await self.bot.warn_bot_channel(ctx): return
            print(f"purging lurkers in server {ctx.guild.name}")
            users = list(filter(lambda member: lookup_role(member.roles, 'approved') is not None, ctx.guild.members))
            print(f"found {len(users)} lurkers")
            await ctx.send(f"found {len(users)} lurkers")


    class AnimeCog(commands.Cog):
        def __init__(self, bot: commands.Bot):
            self.bot = bot

        @commands.Cog.listener()
        async def on_message(self, message: discord.Message) -> None:
            if isinstance(message.channel, discord.TextChannel) and message.channel.name == self.bot.config['channels']['anime']:
                if random.randrange(0, 50) == 0:
                    rand = random.choice([1, 2, 3])
                    if rand == 1:
                        await message.add_reaction('🚫')
                        await message.add_reaction('🇦')
                        await message.add_reaction('🇳')
                        await message.add_reaction('🇮')
                        await message.add_reaction('🇲')
                        await message.add_reaction('🇪')
                    elif rand == 2:
                        message.channel.send(file=discord.File("./assets/images/anime.png"))
                    elif rand == 3:
                        message.channel.send(file=discord.File("./assets/images/yohjiman.png"))

    class AnnoyingCog(commands.Cog):
        def __init__(self, bot: commands.Bot):
            self.bot = bot

        @commands.Cog.listener()
        async def on_message(self, message: discord.Message) -> None:
            if re.match(r'^[^\w]?(yo)?ur mom.*$', message.content.lower()): await message.delete()

    class NoveltyCog(commands.Cog):
        def __new__(cls, bot=commands.Bot, *args, **kwargs):
            cls.create_link_commands(bot.config['commands']['links'])
            cls.create_image_commands(bot.config['commands']['images'])
            return super().__new__(cls, *args, **kwargs)

        def __init__(self, bot: commands.Bot):
            super().__init__()
            self.bot = bot

        @classmethod
        def add_command_fn(cls, name: str, action: Callable[[commands.Context], None]) -> None:
            @commands.command(name=name, hidden=True)
            async def fn(self, ctx: commands.Context):
                print(name)
                await action(ctx)
            setattr(cls, name, fn)
            fn.__name__ = name
            cls.__cog_commands__.append(fn)

        @staticmethod
        def link_command(link: str) -> Callable:
            async def fn(ctx: commands.Context) -> None:
                await ctx.send(link)
            return fn

        @staticmethod
        def image_command(image: str) -> Callable:
            async def fn(ctx: commands.Context) -> None:
                file = discord.File(f"./assets/images/{image}")
                await ctx.send(file=file)
            return fn

        @classmethod
        def create_link_commands(cls, links: list) -> None:
            if not len(links): return
            for cmd, link in links.items():
                cls.add_command_fn(cmd, cls.link_command(link))

        @classmethod
        def create_image_commands(cls, images: list) -> None:
            if not len(images): return
            for cmd, image in images.items():
                cls.add_command_fn(cmd, cls.image_command(image))

        @commands.command(hidden=True)
        async def buttmuscle(self, ctx: commands.Context) -> None:
            print('buttmuscle')
            filename = "./assets/images/buttmusclespicy.jpg" if ctx.channel.name == 'afterdark' else "./assets/images/buttmuscle.jpg"
            await ctx.send(file=discord.File(filename))
            await ctx.send(content='http://buttmuscle.eu/')

        @commands.command(hidden=True)
        async def katon(self, ctx: commands.Context) -> None:
            print('katon')
            user_distinct = distinct(ctx.author)
            if user_distinct == 'Katon#6969':
                filename = "./assets/images/katonkaton.png"
            elif user_distinct == 'brissings#4367':
                filename = "./assets/images/katonbrissings.png"
            else:
                filename = "./assets/images/katon.png"
            await ctx.send(file=discord.File(filename))

        @commands.command(hidden=True)
        async def fakegeekgirls(self, ctx: commands.Context) -> None:
            print('fakegeekgirls')
            if not await self.bot.warn_meta_channel(ctx): return
            await ctx.send("https://discord.gg/agJ6vUD")

        @commands.command(hidden=True)
        async def bayareameetup(self, ctx: commands.Context) -> None:
            print('bayareameetup')
            if not await self.bot.warn_meta_channel(ctx): return
            await ctx.send("https://discord.gg/ySmcTZD")

    ########## SUPPORT

    # class Pruner():
    #     def __init__(self, channel: discord.TextChannel, before: datetime = None):
    #         self.channel = channel
    #         self.before = before
    #         self.stop = False

    #     async def prune(self) -> None:
    #         print(f'pruner pruning {self.channel}')
    #         async for message in self.channel.history(limit=100, before=self.before):
    #             print(message)
    #             await self.delete_message(message)
    #             print('done deleting that message')
    #             if self.stop: break
    #             # await asyncio.sleep(10)
    #         pass

    #     def stop(self) -> None:
    #         self.stop = True

    #     async def delete_message(self, message: discord.Message) -> None:
    #         if self.check_message(message): await message.delete()

    #     def check_message(self, message: discord.Message) -> bool:
    #         print(f"message.created_at: {message.created_at}")
    #         print(f"self.before: {self.before}")
    #         return not self.before or message.created_at < self.before

class Roler():
    def __init__(self, ctx: commands.Context):
        self.ctx = ctx

    async def list_roles(self) -> None:
        config_roles = self.config_roles()
        if not config_roles:
            await self.ctx.send('no roles defined')
            return
        for key, roles in config_roles.items():
            await self.ctx.send(f"{key}: {', '.join(roles)}")

    async def add_roles(self, roles: list) -> None:
        if not self.check_user_approved: return
        if not self.check_config_roles_defined: return

        roles = RolesList(roles)
        flat_config_roles = self.flat_config_roles()
        valid = set(roles) & set(flat_config_roles)
        invalid = set(roles) - set(flat_config_roles)

        if not self.check_bannable(invalid):
            await self.ctx.send(f"you have been banned")
            return

        if valid:
            await self.ctx.send(f"adding to {', '.join(valid)}")
            svalid = lookup_roles(self.ctx.guild.roles, valid)
            print(f"svalid: {svalid}")
            if svalid: await self.ctx.author.add_roles(*svalid)
        if invalid:
            await self.ctx.send(f"not adding to {', '.join(invalid)}")

    async def remove_roles(self, roles: list) -> None:
        if not self.check_user_approved: return
        if not self.check_config_roles_defined: return

        roles = RolesList(roles)
        flat_config_roles = self.flat_config_roles()
        valid = set(roles) & set(flat_config_roles)
        invalid = set(roles) - set(flat_config_roles)

        if not self.check_bannable(invalid):
            await self.ctx.send(f"you have been banned")
            return

        if valid:
            await self.ctx.send(f"removing from {', '.join(valid)}")
            svalid = lookup_roles(self.ctx.guild.roles, valid)
            print(f"svalid: {svalid}")
            if svalid: await self.ctx.author.remove_roles(*svalid)
        if invalid:
            await self.ctx.send(f"not removing from {', '.join(invalid)}")

    def check_user_approved(self) -> bool:
        return self.ctx.bot.lookup_role(self.ctx.author.roles, 'approved') is not None

    def check_config_roles_defined(self) -> bool:
        return self.ctx.bot.config['roles'] is not None

    def config_roles(self) -> list:
        return self.ctx.bot.config['roles']

    def check_bannable(self, invalid) -> bool:
        return not any(role in self.bannable_roles() for role in invalid)

    def flat_config_roles(self) -> list:
        roles = self.ctx.bot.config['roles'].values()
        roles = list(itertools.chain.from_iterable(roles))
        roles = list(map(lambda role: role.lower(), roles))
        return roles

    def bannable_roles(self) -> list:
        return ['mod', 'blackname', 'dad', 'fuzz', 'admin', 'bot', 'approved', 'losers', 'illuminatus', 'anime', 'weeb', 'weebs']

class RolesList(UserDict):
    def __init__(self, data):
        data = map(lambda role: role.split(','), data)
        data = itertools.chain.from_iterable(data)
        data = map(lambda role: re.sub(r'[\s,@]', '', role), data)
        data = map(lambda role: role.lower(), data)
        self.data = list(data)

if __name__ == '__main__':
    EhfBot(Config(r'config/app.yml')).run()
