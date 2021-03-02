import discord
from discord.ext import commands, tasks

from fuzzy import Fuzzy

class Learns(Fuzzy.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def learn (self, ctx: Fuzzy.Context, arg: str):
        """Learns a custom command"""
        await ctx.send(arg)