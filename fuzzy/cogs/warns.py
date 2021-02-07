from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands

from fuzzy import Fuzzy
from fuzzy.models import Infraction, DBUser, InfractionType


class Warns(Fuzzy.Cog):

    def __init__(self, *args):
        super().__init__(*args)

    @commands.command()
    async def warn(self,
                   ctx: Fuzzy.Context,
                   who: commands.Greedy[discord.Member],
                   reason: Optional[str] = ""):
        """Issue a warning to a user.
        'who' is space-separated list of discord users that are to be warned. This can be an ID, a user mention, or
        their name
        'reason' is the reason why they are being warned. This is optional and can be updated
        later with `$pfxreason`"""
        warned_members = []
        for member in who:  # type: discord.Member
            infraction = Infraction.create(ctx, member, reason, InfractionType.WARN)
            infraction = ctx.db.infractions.save(infraction)
            if infraction is not None:
                warned_members.append(f"{member.mention}: Warning ID {infraction.id}")

        warn_string = "\n".join(warned_members)
        await ctx.reply(title="Warning",
                        msg=f"**Reason:** {reason}\n"
                            f"{warn_string}",
                        color=ctx.Color.I_GUESS
                        )
