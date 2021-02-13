from datetime import datetime
from typing import List, Optional

import discord
from discord.ext import tasks, commands

from fuzzy import Fuzzy
from fuzzy.fuzzy import ParseableTimedelta
from fuzzy.models import Lock, DBUser


class Locks(Fuzzy.Cog):
    def __init__(self, *args):
        self.execute_expired_locks.start()  # pylint: disable=no-member
        super().__init__(*args)

    @tasks.loop(seconds=0.5)
    async def execute_expired_locks(self):
        locks: List[Lock] = self.bot.db.locks.find_expired_locks()
        for lock in locks:
            guild: discord.Guild = await self.bot.fetch_guild(lock.guild.id)
            channel: discord.TextChannel = None
            everyone_role: discord.Role = None
            if guild:
                channel = guild.get_channel(lock.channel_id)
                everyone_role = guild.get_role(lock.guild.id)
            if channel and everyone_role:
                await channel.set_permissions(everyone_role, send_messages=lock.previous_value)
            await self.bot.post_log(guild,
                                    msg=f"{channel.mention} was unlocked by {self.bot.user.display_name}",
                                    color=self.bot.Context.Color.GOOD)
            self.bot.db.locks.delete(lock.channel_id)

    @commands.command()
    async def lock(self, ctx: Fuzzy.Context, channels: Optional[commands.Greedy[discord.TextChannel]],
                   time: ParseableTimedelta, reason: Optional[str] = ""):
        active_locks = []
        previous_values = {}
        if channels:
            for channel in channels:
                lock = ctx.db.locks.find_by_id(channel.id)
                if lock:
                    active_locks.append(lock)
                    previous_values[channel.id] = lock.previous_value
        else:
            active_locks.append(ctx.db.locks.find_by_id(ctx.channel.id))

        if active_locks:
            for lock in active_locks:
                ctx.db.locks.delete(lock.channel_id)

        locks = []
        everyone_role: discord.Role = ctx.guild.get_role(ctx.guild.id)
        for channel in channels:
            locks.append(Lock(channel.id or ctx.channel.id,
                              previous_values[channel.id]
                              if channel.id in previous_values.values()
                              else channel.overwrites_for(everyone_role).read_messages,
                              DBUser(ctx.author.id, f"{ctx.author.name}#{ctx.author.discriminator}"),
                              ctx.guild.id,
                              reason,
                              datetime.utcnow() + time))
