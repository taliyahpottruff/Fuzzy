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
        warned_members = []
        for member in who:  # type: discord.Member
            infraction = Infraction(None,
                                    DBUser(member.id, f"{member.name}#{member.discriminator}"),
                                    DBUser(member.id, f"{ctx.author.name}#{ctx.author.discriminator}"),
                                    ctx.guild.id,
                                    reason,
                                    datetime.utcnow(),
                                    InfractionType.WARN,
                                    None)
            infraction = ctx.db.infractions.save(infraction)
            if infraction is not None:
                warned_members.append(f"{member.mention}: Warning ID {infraction.id}")

        warn_string = "\n".join(warned_members)
        await ctx.reply(title="Warning",
                        msg=f"**Reason:** {reason}\n"
                            f"{warn_string}",
                        color=ctx.Color.I_GUESS
                        )
