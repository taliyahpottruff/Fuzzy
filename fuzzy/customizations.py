import enum
import logging
import random
import re
from datetime import timedelta
from typing import Union

import discord
from discord import Activity, ActivityType
from discord.ext import commands

from databases import Database


class AnticipatedError(Exception):
    """An error we expected."""


class UnableToComply(AnticipatedError):
    """We understood what the user wants, but can't."""

    TEXT = "Unable to comply."


class Unauthorized(AnticipatedError):
    """We understood what the user wants, but they aren't allowed to do it."""

    TEXT = "Unauthorized."


class PleaseRestate(AnticipatedError):
    """We didn't understand what the user wants."""

    TEXT = "Please restate query."


class Fuzzy(commands.Bot):
    """
    This Class is mostly just a standard discord.py bot class but sets up additional configuration needed for this bot.
    """

    class Context(commands.Context):
        """
        A context that does other useful things.
        """

        class Color(enum.IntEnum):
            """Colors used by Fuzzy."""

            GOOD = 0x7DB358
            I_GUESS = 0xF9AE36
            BAD = 0xD52D48
            AUTOMATIC_BLUE = 0x1C669B

        @property
        def log(self) -> logging.Logger:
            """Return a logger that's associated with the current cog and command."""
            name = self.command.name.replace(self.bot.config["discord"]["prefix"], "")
            if not self.cog:
                return self.bot.log.getChild(name)

            return self.cog.log.getChild(name)

        @property
        def db(self) -> Database:
            """Return the bot's database connection."""
            return self.bot.db

        async def reply(
            self,
            msg: str = None,
            title: str = discord.Embed.Empty,
            subtitle: str = None,
            color: Color = Color.GOOD,
            embed: discord.Embed = None,
            delete_after: float = None,
        ):
            """Helper for sending embedded replies"""
            if not embed:
                if not subtitle:
                    subtitle = discord.Embed.Empty

                lines = str(msg).split("\n")
                buf = ""
                for line in lines:
                    if len(buf + "\n" + line) > 2048:
                        await self.send(
                            "",
                            embed=discord.Embed(
                                color=color, description=buf, title=title
                            ).set_footer(text=subtitle),
                            delete_after=delete_after,
                        )
                        buf = ""
                    else:
                        buf += line + "\n"

                if len(buf) > 0:
                    return await self.send(
                        "",
                        embed=discord.Embed(
                            color=color, description=buf, title=title
                        ).set_footer(text=subtitle),
                        delete_after=delete_after,
                    )

            return await self.send("", embed=embed, delete_after=delete_after)

        def privileged_modify(
            self,
            subject: Union[
                discord.TextChannel, discord.Member, discord.Guild, discord.Role
            ],
        ) -> bool:
            """
            Check if the context's user can do privileged actions on the subject.
            """
            if self.bot.owner_id == self.author.id:
                return True

            kind = subject.__class__
            if kind in (discord.TextChannel, discord.CategoryChannel):
                return self.author.permissions_in(subject).manage_messages
            if kind == discord.Member:
                return self.author.guild_permissions.ban_users
            if kind == discord.Guild:
                return self.author.guild_permissions.manage_guild
            if kind == discord.Role:
                return self.author.guild_permissions.manage_roles and (
                    self.author.top_role > subject or self.guild.owner == self.author
                )

            raise ValueError(f"unsupported subject {kind}")

    class Cog(commands.Cog):
        """
        A cog with a logger attached to it.
        """

        def __init__(self, bot):
            self.bot: Fuzzy = bot
            self.log = bot.log.getChild(self.__class__.__name__)

    def __init__(self, config, database: Database, **kwargs):
        self.config = config
        self.db: Database = database

        self.log = logging.getLogger("Fuzzy")
        self.log.setLevel(logging.INFO)

        super().__init__(command_prefix=config["discord"]["prefix"], **kwargs)

    @staticmethod
    def random_status() -> Activity:
        """Return a silly status to show to the world"""
        return random.choice(
            [
                Activity(type=ActivityType.watching, name="and eating donuts."),
                Activity(type=ActivityType.listening, name="to those with power.",),
            ]
        )

    async def post_log(self, guild: discord.Guild, *args, **kwargs):
        """Post a log entry to a guild, usage same as ctx.reply"""
        configuration = self.db.guilds.find_by_id(guild.id)
        if not configuration:
            return

        channel = self.get_channel(configuration.mod_log)
        await self.Context.reply(self.get_channel(channel), *args, **kwargs)


class ParseableTimedelta(timedelta):
    """Just timedelta but with support for the discordpy converter thing."""

    @classmethod
    async def convert(cls, _ctx: Fuzzy.Context, argument: str):
        """
        Convert a string in the form [NNNd] [NNNh] [NNNm] [NNNs] into a
        timedelta.
        """

        delta = cls()

        daysm = re.search(r"(\d+) ?d(ays?)?", argument)
        if daysm:
            delta += cls(days=int(daysm[1]))

        hoursm = re.search(r"(\d+) ?h(ours?)?", argument)
        if hoursm:
            delta += cls(hours=int(hoursm[1]))

        minsm = re.search(r"(\d+) ?m((inutes?)?|(ins?)?)?", argument)
        if minsm:
            delta += cls(minutes=int(minsm[1]))

        secsm = re.search(r"(\d+) ?s((econds?)?|(ecs?)?)?", argument)
        if secsm:
            delta += cls(seconds=int(secsm[1]))

        return delta
