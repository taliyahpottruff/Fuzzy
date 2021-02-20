import asyncio
import typing
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
        await asyncio.sleep(0.5)

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
        msg = (
            f"**Banned:** {infraction.user.name} (ID {infraction.user.id})\n"
            f"**Mod:** <@{infraction.moderator.id}>\n"
            f"**Reason:** {infraction.reason or '(no reason specified)'}\n"
        )
        msg += (
            f"This can be published to the published to the public log channel with "
            f"`{self.bot.command_prefix}publish ban {infraction.id}`"
            if infraction.reason
            else f"Reason can be updated with "
            f"`{self.bot.command_prefix}reason {infraction.id} <your reason here>`"
        )
        await self.bot.post_log(
            guild,
            title=f"Ban #{infraction.id}",
            msg=msg,
            color=self.bot.Context.Color.BAD,
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """Posts an unban to the Log channel."""
        infraction = self.bot.db.infractions.find_recent_ban_by_id(user.id, guild.id)

        await self.bot.post_log(
            guild,
            title=f"Unban  #{infraction.id}",
            msg=f"{user.name} (ID {user.id})\n"
            f"`{self.bot.command_prefix}pardon {infraction.id} <reason>` to add an unban reason."
            f"Then `{self.bot.command_prefix}publish unban {infraction.id}` to publish to public log channel.",
            color=self.bot.Context.Color.GOOD,
        )

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def ban(
        self,
        ctx: Fuzzy.Context,
        who: commands.Greedy[typing.Union[discord.Member, discord.User]],
        *,
        reason: Optional[str] = "",
    ):
        """Bans a user from the server.
        `who` is a space-separated list of users. This can be mentions, ids or names.
        `reason` is the reason for the ban. This can be updated later with ${pfx}reason"""
        banned_users = []
        insufficient_permissions = []
        for user in who:  # type: discord.User
            if await self.check_if_can_ban(user):
                if user.id != ctx.author.id:
                    infraction = Infraction.create(
                        ctx, user, reason, InfractionType.BAN
                    )
                    infraction = ctx.db.infractions.save(infraction)
                    if infraction:
                        banned_users.append(
                            f"{infraction.user.name}: Ban ID {infraction.id}"
                        )
                        try:
                            await self.bot.direct_message(
                                user,
                                title=f"Ban ID {infraction.id}",
                                msg=f"You have been banned from {ctx.guild.name} "
                                + (f'for "{reason}"' if reason else ""),
                            )
                        except discord.Forbidden or discord.HTTPException:
                            pass
                    try:
                        await ctx.guild.ban(user, reason=reason, delete_message_days=0)
                    except discord.Forbidden:
                        pass

                else:
                    await ctx.reply("You cant ban yourself.")
            else:
                insufficient_permissions.append(user)

        ban_string = "\n".join(banned_users)
        if banned_users:
            await ctx.reply(
                title="Banned",
                msg=(f"**Reason:** {reason}\n" if reason else "") + f"{ban_string}",
                color=ctx.Color.BAD,
            )
        if insufficient_permissions:
            await ctx.reply(
                f"Insufficient permissions to ban the following users: "
                f"{' '.join(user.mention for user in insufficient_permissions)}"
            )

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def unban(self, ctx: Fuzzy.Context, who: commands.Greedy[discord.User]):
        """Unbans a user from the server. This does not pardon the infraction automatically. use ${pfx}pardon to
        do that.
        `who` is a space-separated list of users. This can be mentions, ids or names."""
        unbanned_users = []
        for user in who:  # type: discord.User
            await ctx.guild.unban(user)
            infraction = ctx.db.infractions.find_recent_ban_by_id(user.id, ctx.guild.id)
            if infraction:
                unbanned_users.append(f"{infraction.user.name}: Ban ID {infraction.id}")
                try:
                    await self.bot.direct_message(
                        user,
                        title=f"Unban ID {infraction.id}",
                        msg=f"You have been unbanned from {ctx.guild.name}",
                    )
                except discord.Forbidden or discord.HTTPException:
                    pass

        unban_string = "\n".join(unbanned_users)
        await ctx.reply(
            title="Unbanned", msg=f"{unban_string}", color=ctx.Color.GOOD,
        )

    async def check_if_can_ban(
        self, member: typing.Union[discord.Member, discord.User]
    ):
        if isinstance(member, discord.User):
            return True
        guild: discord.Guild = member.guild
        bot_member_account: discord.Member = await member.guild.fetch_member(
            self.bot.user.id
        )
        return (
            guild.roles.index(bot_member_account.roles[-1])
            > guild.roles.index(member.roles[-1])
            and guild.owner_id != member.id
        )
