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
            # noinspection PyTypeChecker
            channel: discord.TextChannel = None
            # noinspection PyTypeChecker
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
        locks = []
        everyone_role: discord.Role = ctx.guild.get_role(ctx.guild.id)
        if not channels:
            channels = [ctx.channel]
        for channel in channels:
            ctx.db.locks.save(
                Lock(channel.id or ctx.channel.id,
                     channel.overwrites_for(everyone_role).read_messages,
                     DBUser(ctx.author.id, f"{ctx.author.name}#{ctx.author.discriminator}"),
                     ctx.guild.id,
                     reason,
                     datetime.utcnow() + time)
            )
            locks.append(f"{channel.mention}")
            await channel.set_permissions(everyone_role, send_messages=False)
        if not locks:
            await ctx.reply("Could not find any channels with those IDs.")
            return
        await ctx.reply(f"Locked the following channels for {time}: {' '.join(locks)}")
        await self.bot.post_log(ctx.guild,
                                msg=f"{ctx.author.name}#{ctx.author.discriminator} "
                                    f"locked {' '.join(locks)} for {time} for {reason}")

    @commands.command()
    async def unlock(self, ctx: Fuzzy.Context, channels: Optional[commands.Greedy[discord.TextChannel]]):
        unlocks = []
        everyone_role: discord.Role = ctx.guild.get_role(ctx.guild.id)
        if not channels:
            channels = [ctx.channel]
        for channel in channels:
            lock = ctx.db.locks.find_by_id(channel.id)
            await channel.set_permissions(everyone_role, send_message=lock.previous_value)
            ctx.db.locks.delete(lock.channel_id)
            unlocks.append(channel.mention)
        if not unlocks:
            await ctx.reply("Could not find any channels with those IDs.")
            return
        await ctx.reply(f"Unlocked the following channels: {' '.join(unlocks)}")
        await self.bot.post_log(ctx.guild,
                                msg=f"{ctx.author.name}#{ctx.author.discriminator} "
                                    f"unlocked {' '.join(unlocks)}")