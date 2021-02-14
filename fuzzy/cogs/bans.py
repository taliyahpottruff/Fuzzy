import asyncio
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands

from fuzzy import Fuzzy
from fuzzy.models import Infraction, InfractionType, DBUser


class Bans(Fuzzy.Cog):
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Posts a ban to the Log channel. Checks to see if Fuzzy was used for ban and if not, creates a new
        infraction log."""
        await asyncio.sleep(5.0)

        infraction = self.bot.db.infractions.find_recent_ban_by_id(user.id, guild.id)

        if not infraction:
            # noinspection PyTypeChecker
            infraction = self.bot.db.infractions.save(
                Infraction(
                    None,
                    DBUser(user.id, f"{user.name}#{user.discriminator}"),
                    DBUser(0, "Unknown#????"),
                    self.bot.db.guilds.find_by_id(guild.id),
                    "",
                    datetime.utcnow(),
                    InfractionType.BAN,
                    None,
                    None,
                    None,
                )
            )
        await self.bot.post_log(
            guild,
            title=f"{infraction.moderator.name} (ID {infraction.moderator.id})",
            msg=f"**Banned** {infraction.user.name} (ID {infraction.user.id})\n"
            f"**Reason:** {infraction.reason or '(no reason specified)'}",
            color=self.bot.Context.Color.BAD,
            subtitle=(
                f"This can be published to the published to the public log channel with "
                f"`{self.bot.command_prefix}publish ban {infraction.id}`"
                if infraction.reason
                else f"Reason can be updated with "
                f"`{self.bot.command_prefix}reason {infraction.id} <your reason here>`"
            ),
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """Posts an unban to the Log channel."""
        infraction = self.bot.db.infractions.find_recent_ban_by_id(user.id, guild.id)

        await self.bot.post_log(
            guild,
            title=f"**Unbanned**",
            msg=f"{user.name} (ID {user.id})\n"
            f"`{self.bot.command_prefix}pardon {infraction.id} <reason>` to add an unban reason."
            f"Then `{self.bot.command_prefix}publish unban {infraction.id}` to publish to public log channel.",
            color=self.bot.Context.Color.GOOD,
        )

    @commands.command()
    async def ban(
        self,
        ctx: Fuzzy.Context,
        who: commands.Greedy[discord.User],
        reason: Optional[str] = "",
    ):
        """Bans a user from the server.
        `who` is a space-separated list of users. This can be mentions, ids or names.
        `reason` is the reason for the ban. This can be updated later with ${pfx}reason"""
        banned_users = []
        for user in who:  # type: discord.Member
            await ctx.guild.ban(user, reason=reason, delete_message_days=0)
            infraction = Infraction.create(ctx, user, reason, InfractionType.BAN)
            infraction = ctx.db.infractions.save(infraction)
            if infraction:
                banned_users.append(f"{infraction.user}: Ban ID {infraction.id}")

        ban_string = "\n".join(banned_users)
        await ctx.reply(
            title="Banned",
            msg=(f"**Reason:** {reason}\n" if reason else "") + f"{ban_string}",
            color=ctx.Color.BAD,
        )
        await self.bot.post_log(
            ctx.guild,
            msg=f"{ctx.author.name}#{ctx.author.discriminator} "
            f"banned: {ban_string} " + (f"for {reason}" if reason else ""),
            color=ctx.Color.BAD,
        )

    @commands.command()
    async def unban(self, ctx: Fuzzy.Context, who: commands.Greedy[discord.User]):
        """Unbans a user from the server. This does not pardon the infraction automatically. use ${pfx}pardon to
        do that.
        `who` is a space-separated list of users. This can be mentions, ids or names."""
        unbanned_users = []
        for user in who:  # type: discord.Member
            await ctx.guild.unban(user)
            infraction = ctx.db.infractions.find_recent_ban_by_id(user.id, ctx.guild.id)
            if infraction:
                unbanned_users.append(f"{infraction.user}: Ban ID {infraction.id}")

        unban_string = "\n".join(unbanned_users)
        await ctx.reply(
            title="Unbanned", msg=f"{unban_string}", color=ctx.Color.GOOD,
        )
        await self.bot.post_log(
            ctx.guild,
            msg=f"{ctx.author.name}#{ctx.author.discriminator} "
            f"unbanned: {unban_string} ",
            color=ctx.Color.GOOD,
        )
