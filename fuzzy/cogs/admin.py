from typing import Optional

import discord
from discord.ext import commands

from fuzzy import Fuzzy
from fuzzy.models import DurationType


class Admin(Fuzzy.Cog):
    @commands.group()
    async def admin(self, ctx: Fuzzy.Context):
        """Administration Module for bot. Updates the various settings for this server."""

    @commands.command(parent=admin)
    async def log(self, ctx: Fuzzy.Context, channel: Optional[discord.TextChannel]):
        if not channel:
            channel = ctx.channel
        guild = ctx.db.guilds.find_by_id(ctx.guild.id)
        guild.mod_log = channel.id
        ctx.db.guilds.save(guild)
        await ctx.reply(f"Updated the mod log channel to {channel.mention}")

    @commands.command(parent=admin)
    async def public_log(
        self, ctx: Fuzzy.Context, channel: Optional[discord.TextChannel]
    ):
        if not channel:
            channel = ctx.channel
        guild = ctx.db.guilds.find_by_id(ctx.guild.id)
        guild.public_log = channel.id
        ctx.db.guilds.save(guild)
        await ctx.reply(f"Updated the public log channel to {channel.mention}")
        await self.bot.post_log(
            ctx.guild,
            msg=f"{ctx.author.name}#{ctx.author.discriminator} updated public log channel to {channel.mention}",
        )

    @commands.command(parent=admin)
    async def auto_pardon(self, ctx: Fuzzy.Context, time: str):
        guild = ctx.db.guilds.find_by_id(ctx.guild.id)
        duration_type = None
        if time[-1].lower() == "d":
            duration_type = DurationType.DAYS
        if time[-1].lower() == "m":
            duration_type = DurationType.MONTHS
        if time[-1].lower() == "y":
            duration_type = DurationType.YEARS
        guild.duration_type = duration_type
        guild.duration = int(time[:-1])
        ctx.db.guilds.save(guild)
        await ctx.reply(f"Infractions will auto pardon now after {time}")
        await self.bot.post_log(
            ctx.guild,
            msg=f"{ctx.author.name}#{ctx.author.discriminator} updated auto pardon to {time}",
        )

    @commands.group(parent=admin)
    async def mutes(self, ctx: Fuzzy.Context):
        """Updates and manages the Mute role used by the mute module."""

    @commands.command(parent=mutes)
    async def set(self, ctx: Fuzzy.Context, role: discord.Role):
        """This will assign an already existing role as the role to use for muting a member.
        This is useful if you have used a different moderation bot previously and would like to reuse that role.
        `role` is a mention, id or name of a role to use for muting."""
        guild = ctx.db.guilds.find_by_id(ctx.guild.id)
        guild.mute_role = role.id
        ctx.db.guilds.save(guild)
        await ctx.reply(
            f"{self.bot.user.display_name} will now use {role.name} when muting someone."
        )
        await self.bot.post_log(
            ctx.guild,
            msg=f"{ctx.author.name}#{ctx.author.discriminator} updated mute role to {role.name}",
        )

    @commands.command(parent=mutes)
    async def create(self, ctx: Fuzzy.Context):
        """This creates a new role for muting. It will go through every channel and category on the server and
        add this role as an override that blocks 'Send Messages' permissions"""
        guild = ctx.db.guilds.find_by_id(ctx.guild.id)
        role = await ctx.guild.create_role(name="Mute", color=0x818386)
        guild.mute_role = role.id
        ctx.db.guilds.save(guild)

        for channel in ctx.guild.channels:
            if (
                isinstance(channel, discord.TextChannel)
                and not channel.permissions_synced
            ):
                await channel.set_permissions(role, send_messages=False)
        for category in ctx.guild.categories:
            await category.set_premissions(role, send_messages=False)

        await ctx.reply(
            f"{self.bot.user.display_name} will now use {role.name} when muting someone."
        )
        await self.bot.post_log(
            ctx.guild,
            msg=f"{ctx.author.name}#{ctx.author.discriminator} created mute {role.name}",
        )

    @commands.command(parent=mutes)
    async def refresh(self, ctx: Fuzzy.Context):
        """This refreshes the permissions of the mute role. It will go through every channel and
        category on the server and add this role as an override that blocks 'Send Messages' permissions"""
        guild = ctx.db.guilds.find_by_id(ctx.guild.id)
        role = await ctx.guild.create_role(name="Mute", color=0x818386)
        guild.mute_role = role.id
        ctx.db.guilds.save(guild)

        for channel in ctx.guild.channels:
            if (
                isinstance(channel, discord.TextChannel)
                and not channel.permissions_synced
            ):
                await channel.set_permissions(role, send_messages=False)
        for category in ctx.guild.categories:
            await category.set_premissions(role, send_messages=False)

        await ctx.reply(
            f"{role.mention} permissions have been refreshed on the server. If issues persist "
            f" check if a role the user has gives them explict 'Send Messages' permissions"
        )
        await self.bot.post_log(
            ctx.guild,
            msg=f"{ctx.author.name}#{ctx.author.discriminator} refreshed permissions on {role.name}",
        )
