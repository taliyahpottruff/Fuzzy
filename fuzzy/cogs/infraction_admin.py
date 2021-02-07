from discord.ext import commands

from fuzzy import Fuzzy
from fuzzy.fuzzy import UnableToComply
from fuzzy.models import *


class InfractionAdmin(Fuzzy.Cog):

    def __init__(self, *args):
        super().__init__(*args)

    @commands.command()
    async def pardon(self,
                     ctx: Fuzzy.Context,
                     infraction_ids: commands.Greedy[int]):
        """Pardon a user's infraction. This will leave the infraction in the logs but will mark it as pardoned.
        This command cannot pardon bans as those will automatically be pardoned when a user is unbanned.

        'infraction_ids' is a space-separated list of Infraction IDs that are to be pardoned
        """
        all_infractions = []
        all_errors = []
        all_bans = []
        for infraction_id in infraction_ids:
            infraction: Infraction = ctx.db.infractions.find_by_id(infraction_id)
            if infraction is not None and infraction.infraction_type != InfractionType.BAN:
                all_infractions.append(infraction)
            elif infraction.infraction_type == InfractionType.BAN:
                all_bans.append(str(infraction.id))
            else:
                all_errors.append(f"{infraction_id}")
        if not all_infractions:
            raise UnableToComply("Could not find any Warns or Mutes with those IDs.")
        all_pardons = []

        for infraction in all_infractions:
            pardon = Pardon(infraction.id,
                            DBUser(ctx.author.id, f"{ctx.author.name}#{ctx.author.discriminator}"),
                            datetime.utcnow())
            pardon = ctx.db.pardons.save(pardon)
            if pardon is not None:
                infraction.pardon = pardon
                all_pardons.append(infraction)
            else:
                all_errors.append(infraction.id)
        if all_errors or all_bans:
            msg = ""
            if all_bans:
                msg += "Cannot Pardon Bans, Please use Unban: " + " ".join(all_bans) + "\n"
            if all_errors:
                msg += "Error Processing Pardons: " + " ".join(all_errors)
            await ctx.reply(msg, color=ctx.Color.I_GUESS)

        if all_pardons:
            msg = ""
            for infraction in all_pardons:
                msg += f"**ID:** {infraction.id} **User:** {infraction.user.name}\n"

            await ctx.reply(title="Pardoned", msg=msg, color=ctx.Color.GOOD)

    @commands.command()
    async def forget(self,
                     ctx: Fuzzy.Context,
                     infraction_ids: commands.Greedy[int]):
        """Forgets a user's infraction. This will permanently remove the infraction from the logs.

        'infraction_ids' is a space-separated list of Infraction IDs that are to be forgotten.
        """
        all_infractions = []
        all_errors = []
        for infraction_id in infraction_ids:
            infraction: Infraction = ctx.db.infractions.find_by_id(infraction_id)
            if infraction is not None:
                all_infractions.append(infraction)
            else:
                all_errors.append(f"{infraction_id}")
        if not all_infractions:
            raise UnableToComply("Could not find any Infractions with those IDs.")

        for infraction in all_infractions:
            if infraction.pardon is not None:
                ctx.db.pardons.delete(infraction.id)
            ctx.db.infractions.delete(infraction.id)
        if all_errors:
            msg = "Error forgetting: " + " ".join(all_errors)
            await ctx.reply(msg, color=ctx.Color.I_GUESS)
        if all_infractions:
            msg = ""
            for infraction in all_infractions:
                msg += f"**ID:** {infraction.id} **User:** {infraction.user.name}\n"

            await ctx.reply(title="Forgot", msg=msg, color=ctx.Color.GOOD)

    @commands.command()
    async def reason(self,
                     ctx: Fuzzy.Context,
                     infraction_ids: commands.Greedy[int],
                     reason: str):
        """Updates the reason of a user's infraction.

        'infraction_ids' is a space-separated list of Infraction IDs that are to have their reasons updated.
        'reason' is the new reason to be saved to these infractions
        """
        all_infractions = []
        all_errors = []
        for infraction_id in infraction_ids:
            infraction: Infraction = ctx.db.infractions.find_by_id(infraction_id)
            if infraction is not None:
                all_infractions.append(infraction)
            else:
                all_errors.append(f"{infraction_id}")
        if not all_infractions:
            raise UnableToComply("Could not find any Infractions with those IDs.")

        for infraction in all_infractions:
            infraction.reason = reason
            ctx.db.infractions.save(infraction)

        if all_errors:
            msg = "Error Updating Reason: " + " ".join(all_errors)
            await ctx.reply(msg, color=ctx.Color.I_GUESS)
        if all_infractions:
            msg = ""
            for infraction in all_infractions:
                msg += f"{infraction.id} "
            await ctx.reply(f"**Updated Reason to {reason} for: {msg}")
