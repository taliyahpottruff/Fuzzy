from datetime import datetime, timedelta

from discord.ext import commands

from fuzzy import Fuzzy


class Purges(Fuzzy.Cog):
    @commands.command()
    async def purge(self, ctx: Fuzzy.Context, amount: int):
        """Deletes the most recent messages in a channel.
        `amount` is the number of messages to delete."""
        deleted = []
        # while amount > 0:
        deleted += await ctx.channel.purge(
            limit=amount,  # if amount < 100 else 100)
            bulk=True,
            after=(datetime.utcnow() - timedelta(days=14)),
        )
        # amount -= 100
        await ctx.reply(f"Purged {len(deleted)} messages from {ctx.channel.mention}.")
