from typing import List

import discord
from discord.ext import commands

from fuzzy import Fuzzy
from fuzzy.models import Infraction


class Logs(Fuzzy.Cog):
    @commands.group(aliases=["log"])
    async def logs(self, ctx: Fuzzy.Context):
        """Gathers relevant logs from the stored infractions"""

    @commands.command(parent=logs)
    async def all(self, ctx: Fuzzy.Context, who: discord.User):
        """Displays all Infractions of the specified user.
        `who` is the person to grab the infractions for. This can be a mention, ID or name."""
        if not ctx.author.guild_permissions.manage_messages and ctx.author != who:
            await ctx.reply("Insufficient permissions to access someone else's log.")
            return

        all_infraction: List[Infraction] = ctx.db.infractions.find_all_for_user(
            who.id, ctx.guild.id
        )
        if not all_infraction:
            await ctx.reply("User does not have any infractions.")
            return
        fields = Logs.create_infraction_text(all_infraction)
        msgs = Logs.compile_text(fields)
        for msg in msgs:
            embed = discord.Embed(
                title=f"Infractions for {who.name}#{who.discriminator}",
                description=msg,
                color=self.bot.Context.Color.AUTOMATIC_BLUE,
            )
            await ctx.send(embed=embed)

    @commands.command(parent=logs, aliases=["warn"])
    async def warns(self, ctx: Fuzzy.Context, who: discord.User):
        """Displays all warns of the specified user.
        `who` is the person to grab the warns for. This can be a mention, ID or name."""
        if not ctx.author.guild_permissions.manage_messages and ctx.author != who:
            await ctx.reply("Insufficient permissions to access someone else's log.")
            return

        all_infraction: List[Infraction] = ctx.db.infractions.find_warns_for_user(
            who.id, ctx.guild.id
        )
        if not all_infraction:
            await ctx.reply("User does not have any warns.")
            return
        fields = Logs.create_infraction_text(all_infraction)
        msgs = Logs.compile_text(fields)
        for msg in msgs:
            embed = discord.Embed(
                title=f"Warns for {who.name}#{who.discriminator}",
                description=msg,
                color=self.bot.Context.Color.AUTOMATIC_BLUE,
            )
            await ctx.send(embed=embed)

    @commands.command(parent=logs, aliases=["mute"])
    async def mutes(self, ctx: Fuzzy.Context, who: discord.User):
        """Displays all mutes of the specified user.
        `who` is the person to grab the mutes for. This can be a mention, ID or name."""
        if not ctx.author.guild_permissions.manage_messages and ctx.author != who:
            await ctx.reply("Insufficient permissions to access someone else's log.")
            return

        all_infraction: List[Infraction] = ctx.db.infractions.find_mutes_for_user(
            who.id, ctx.guild.id
        )
        if not all_infraction:
            await ctx.reply("User does not have any mutes.")
            return
        fields = Logs.create_infraction_text(all_infraction)
        msgs = Logs.compile_text(fields)
        for msg in msgs:
            embed = discord.Embed(
                title=f"Mutes for {who.name}#{who.discriminator}",
                description=msg,
                color=self.bot.Context.Color.AUTOMATIC_BLUE,
            )
            await ctx.send(embed=embed)

    @commands.command(parent=logs, aliases=["ban"])
    async def bans(self, ctx: Fuzzy.Context, who: discord.User):
        """Displays all bans of the specified user.
        `who` is the person to grab the bans for. This can be a mention, ID or name."""
        if not ctx.author.guild_permissions.manage_messages and ctx.author != who:
            await ctx.reply("Insufficient permissions to access someone else's log.")
            return

        all_infraction: List[Infraction] = ctx.db.infractions.find_bans_for_user(
            who.id, ctx.guild.id
        )
        if not all_infraction:
            await ctx.reply("User does not have any bans.")
            return
        fields = Logs.create_infraction_text(all_infraction)
        msgs = Logs.compile_text(fields)
        for msg in msgs:
            embed = discord.Embed(
                title=f"Bans for {who.name}#{who.discriminator}",
                description=msg,
                color=self.bot.Context.Color.AUTOMATIC_BLUE,
            )
            await ctx.send(embed=embed)

    @commands.command(parent=logs)
    async def mod(self, ctx: Fuzzy.Context, who: discord.User):
        """Displays all the actions of the specified moderator..
        `who` is the person to grab the actions for. This can be a mention, ID or name."""
        if not ctx.author.guild_permissions.manage_messages and ctx.author != who:
            await ctx.reply("Insufficient permissions to access someone else's log.")
            return

        mod_actions = ctx.db.infractions.find_mod_actions(who.id, ctx.guild.id)
        await ctx.reply(
            title=f"Moderation log for {who.name}#{who.discriminator}",
            msg=f"Bans: {mod_actions['bans']}\n"
            f"Mutes: {mod_actions['mutes']}\n"
            f"Warns: {mod_actions['warns']}",
        )

    @staticmethod
    def create_infraction_text(infractions: List[Infraction]) -> List[str]:
        """creates a list of formatted messages of each infraction given."""
        fields = []
        for infraction in infractions:
            msg = (
                f"**{infraction.id} : {infraction.infraction_type.value}** : "
                f"{infraction.infraction_on.strftime('%b %d, %y at %I:%m %p')}\n"
                f"Reason: {infraction.reason}\n"
                f"Moderator: {infraction.moderator.name}\n"
            )
            if infraction.pardon:
                msg = (
                    f"~~{msg}~~"
                    f"**Pardoned by: {infraction.pardon.moderator.name} on "
                    f"{infraction.pardon.pardon_on.strftime('%b %d, %y at %I:%m %p')}**\n"
                )
            fields.append(msg)
        return fields

    @staticmethod
    def compile_text(incoming_list: List[str]) -> List[str]:
        """takes a list of strings and combines them till the max message size it hit,
        and then creates a new msg."""
        list_to_return = []
        msg = ""
        while incoming_list:
            if len(msg) + len(incoming_list[0]) < 2048:
                msg += incoming_list.pop(0)
            else:
                list_to_return.append(msg)
                msg = ""
            if not incoming_list:
                list_to_return.append(msg)
        return list_to_return
