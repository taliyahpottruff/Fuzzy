from datetime import datetime
from typing import List, Optional

import discord
from discord.ext import tasks, commands

from fuzzy import Fuzzy
from fuzzy.models import Mute, Infraction, InfractionType, DBUser
from ..fuzzy import ParseableTimedelta


class Mutes(Fuzzy.Cog):
    def __init__(self, *args):
        self.execute_expired_mutes.start()  # pylint: disable=no-member
        super().__init__(*args)

    @tasks.loop(seconds=0.5)
    async def execute_expired_mutes(self):
        """Finds expired mutes and unmutes the user"""
        mutes: List[Mute] = self.bot.db.mutes.find_expired_mutes()
        unmuted_users = []
        for mute in mutes:
            guild: discord.Guild = await self.bot.fetch_guild(mute.infraction.guild.id)
            # noinspection PyTypeChecker
            user: discord.Member = None
            # noinspection PyTypeChecker
            mute_role: discord.Role = None
            if guild:
                user = guild.get_member(mute.user.id)
                mute_role = guild.get_role(mute.infraction.guild.mute_role)

            if user and mute_role:
                await user.remove_roles(mute_role)
                self.bot.db.mutes.delete(mute.infraction.id)
                unmuted_users.append(user)
                await self.bot.post_log(
                    guild,
                    msg=f"{mute.user.name} mute expired.",
                    color=self.bot.Context.Color.AUTOMATIC_BLUE,
                )

    @commands.command()
    async def mute(
        self,
        ctx: Fuzzy.Context,
        who: commands.Greedy[discord.Member],
        time: ParseableTimedelta,
        reason: Optional[str],
    ):
        """Mutes users for the specified amount of time.

        `who` is a space-separated list of discord users that are to be muted. This can be an ID, a user mention,
        or their name.

        `time` is a time delta in (d)ays (h)ours (m)inutes (s)econds.
        Number first, and type second i.e.`5h` for 5 hours

        `reason` is the reason for the mute. This is optional and can be updated later with `${pfx}reason`"""
        muted_members = []
        all_errors = []
        mute_role: discord.Role = ctx.guild.fetch_role(
            ctx.db.guilds.find_by_id(ctx.guild.id).mute_role
        )

        for member in who:  # type: discord.Member

            active_mute = ctx.db.mutes.find_active_mute(member.id, ctx.guild.id)
            if active_mute:
                ctx.db.mutes.delete(active_mute.infraction.id)

            infraction = Infraction.create(ctx, member, reason, InfractionType.MUTE)
            infraction = ctx.db.infractions.save(infraction)

            if infraction.id:
                end_time = datetime.utcnow() + time
                mute = Mute(
                    infraction,
                    end_time,
                    DBUser(member.id, f"{member.name}#{member.discriminator}"),
                )
                ctx.db.mutes.save(mute)

                await member.add_roles(mute_role)
                muted_members.append(member.mention)
            else:
                all_errors.append(member.mention)

        msg = ""
        if all_errors:
            msg += "Error muting: " + " ".join(all_errors) + "\n"
        if muted_members:
            msg += (
                f"Muted the following members for {reason}: {' '.join(muted_members)}"
            )

        await ctx.reply(msg, color=ctx.Color.BAD)
        await self.bot.post_log(
            ctx.guild,
            msg=f"{ctx.author.name}#{ctx.author.discriminator} "
            f"muted {' '.join(muted_members)} for {reason}",
            color=ctx.Color.BAD,
        )

    @commands.command()
    async def unmute(self, ctx: Fuzzy.Context, who: commands.Greedy[discord.Member]):
        """Unmutes a user.
        `who` is a space-separated list of discord users that are to be unmuted. This can be an ID< a user mention, or
        their name."""
        unmuted_members = []
        all_errors = []
        for member in who:
            active_mute = ctx.db.mutes.find_active_mute(member.id, ctx.guild.id)
            if active_mute:
                ctx.db.mutes.delete(active_mute.infraction.id)

            mute_role: discord.Role = ctx.guild.fetch_role(
                ctx.db.guilds.find_by_id(ctx.guild.id).mute_role
            )

            if mute_role is None:
                await ctx.reply("Error fetching mute role:")
                return

            if mute_role in member.roles:
                await member.remove_roles(mute_role)
                unmuted_members.append(member.mention)
            else:
                all_errors.append(member.mention)

        msg = ""
        if all_errors:
            msg += f"Could not find active mutes for: {' '.join(all_errors)}\n"
        if unmuted_members:
            msg += f"Unmuted the following users: {' '.join(unmuted_members)}"
        await ctx.reply(msg)
        await self.bot.post_log(
            ctx.guild,
            msg=f"{ctx.author.name}#{ctx.author.discriminator} "
            f"unmuted {' '.join(unmuted_members)}",
            color=ctx.Color.AUTOMATIC_BLUE,
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Checks if a member who joined the server, had a pre=existing mute and reapplies it if necessary."""
        active_mute = self.bot.db.mutes.find_active_mute(member.id, member.guild.id)
        if active_mute:

            mute_role: discord.Role = member.guild.fetch_role(
                self.bot.db.guilds.find_by_id(member.guild.id).mute_role
            )
            if mute_role:
                await member.add_roles(mute_role)
