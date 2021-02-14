from typing import Optional

import discord
from discord.ext import commands

from fuzzy import Fuzzy
from fuzzy.models import Infraction, InfractionType


class Warns(Fuzzy.Cog):
    @commands.command()
    async def warn(
        self,
        ctx: Fuzzy.Context,
        who: commands.Greedy[discord.Member],
        *,
        reason: Optional[str] = "",
    ):
        """Issue a warning to a user.
        `who` is a space-separated list of discord users that are to be warned. This can be an ID, a user mention, or
        their name.
        `reason` is the reason why they are being warned. This is optional and can be updated
        later with `${pfx}reason`"""
        warned_members = []
        for member in who:  # type: discord.Member
            infraction = Infraction.create(ctx, member, reason, InfractionType.WARN)
            infraction = ctx.db.infractions.save(infraction)
            if infraction:
                warned_members.append(f"{member.mention}: Warning ID {infraction.id}")

        warn_string = "\n".join(warned_members)
        await ctx.reply(
            title="Warning",
            msg=(f"**Reason:** {reason}\n" if reason else "") + f"{warn_string}",
            color=ctx.Color.I_GUESS,
        )
        await self.bot.post_log(
            ctx.guild,
            msg=f"{ctx.author.name}#{ctx.author.discriminator} "
            f"warned: {warn_string} " + (f"for {reason}" if reason else ""),
            color=ctx.Color.I_GUESS,
        )
