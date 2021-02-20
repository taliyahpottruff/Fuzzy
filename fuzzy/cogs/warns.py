from typing import Optional

import discord
from discord.ext import commands

from fuzzy import Fuzzy
from fuzzy.models import Infraction, InfractionType


class Warns(Fuzzy.Cog):
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(
            self,
            ctx: Fuzzy.Context,
            who: commands.Greedy[discord.User],
            *,
            reason: Optional[str] = "",
    ):
        """Issue a warning to a user.
        `who` is a space-separated list of discord users that are to be warned. This can be an ID, a user mention, or
        their name.
        `reason` is the reason why they are being warned. This is optional and can be updated
        later with `${pfx}reason`"""
        warned_members = []
        error_sending_dm = []
        for member in who:  # type: discord.User
            if member.id != ctx.author.id:
                infraction = Infraction.create(ctx, member, reason, InfractionType.WARN)
                infraction = ctx.db.infractions.save(infraction)
                if infraction:
                    warned_members.append(f"{member.mention}: Warning **ID {infraction.id}**")
                    try:
                        await self.bot.direct_message(member,
                                                      title=f"Warning ID {infraction.id}",
                                                      msg=f"You have been warned on {ctx.guild.name} " +
                                                          (f'for \"{reason}\"' if reason else ''))
                    except discord.Forbidden or discord.HTTPException:
                        error_sending_dm.append(member)
            else:
                await ctx.reply("You cant warn yourself.")

        warn_string = "\n".join(warned_members)
        await ctx.reply(
            title="Warning",
            msg=(f"**Reason:** {reason}\n" if reason else "") + f"{warn_string}",
            color=ctx.Color.I_GUESS,
        )
        if error_sending_dm:
            await ctx.reply(f"Could not send direct message to the following users: "
                            f"{' '.join(member.mention for member in error_sending_dm)}")
        await self.bot.post_log(
            ctx.guild,
            title="Warn",
            msg=f"**Mod:** {ctx.author.mention}\n" +
                (f"**Reason:** {reason}\n" if reason else "") +
                f"{warn_string} ",
            color=ctx.Color.I_GUESS,
        )
