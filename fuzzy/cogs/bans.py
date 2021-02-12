import asyncio
from datetime import datetime

import discord
from discord.ext import commands

from fuzzy import Fuzzy
from fuzzy.models import Infraction, InfractionType, DBUser


class Bans(Fuzzy.Cog):
    @commands.Cog.listener
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        await asyncio.sleep(5.0)

        infraction = self.bot.db.infractions.find_recent_ban_by_id(user.id, guild.id)

        if not infraction:
            # noinspection PyTypeChecker
            infraction = self.bot.db.infractions.save(
                Infraction(
                    None,
                    DBUser(user.id, f"{user.name}#{user.discriminator}"),
                    DBUser(0, "Unknown#????"),
                    guild.id,
                    "",
                    datetime.utcnow(),
                    InfractionType.BAN,
                    None,
                    None,
                )
            )
        await self.bot.post_log(
            guild,
            title=f"{infraction.moderator.name} (ID {infraction.moderator.id})",
            msg=f"**Banned** {infraction.user.name} (ID {infraction.user.id})\n"
            f"**Reason: {infraction.reason or '(no reason specified)'}",
            color=self.bot.Context.Color.BAD,
            subtitle=(
                "This can be published to the "
                if infraction.reason
                else f"Reason can be updated with "
                f"`{self.bot.command_prefix}reason {infraction.id} <your reason here>`"
            ),
        )
