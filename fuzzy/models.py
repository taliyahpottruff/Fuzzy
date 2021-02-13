from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import discord

from fuzzy import Fuzzy


class DurationType(Enum):
    DAYS = 1
    MONTHS = 2
    YEARS = 3


class InfractionType(Enum):
    WARN = 1
    MUTE = 2
    BAN = 3


class PublishType(Enum):
    BAN = 1
    UNBAN = 2


@dataclass
class GuildSettings(object):
    id: int
    mod_log: int
    public_log: int
    duration_type: DurationType
    duration: int
    mute_role: int


@dataclass()
class DBUser(object):
    id: int
    name: str


@dataclass()
class Pardon(object):
    infraction_id: int
    moderator: DBUser
    pardon_on: datetime
    reason: str


@dataclass()
class PublishedMessage(object):
    infraction_id: int
    message_id: int
    publish_type: PublishType


@dataclass()
class Infraction(object):
    id: int
    user: DBUser
    moderator: DBUser
    guild: GuildSettings
    reason: str
    infraction_on: datetime
    infraction_type: InfractionType
    pardon: Pardon
    published_ban: PublishedMessage
    published_unban: PublishedMessage

    @classmethod
    def create(
        cls,
        ctx: Fuzzy.Context,
        who: discord.Member,
        reason: str,
        infraction_type: InfractionType,
    ):
        """Creates a new Infraction ready to be stored in DB.
        This will not have id pardon or published_ban attributes. Use normal constructor if those are required"""
        # noinspection PyTypeChecker
        return cls(
            None,
            DBUser(who.id, f"{who.name}#{who.discriminator}"),
            DBUser(ctx.author.id, f"{ctx.author.name}#{ctx.author.discriminator}"),
            ctx.guild.id,
            reason,
            datetime.utcnow(),
            infraction_type,
            None,
            None,
            None,
        )


@dataclass()
class Mute(object):
    infraction: Infraction
    end_time: datetime
    user: DBUser


@dataclass()
class Lock(object):
    channel_id: int
    previous_value: bool
    moderator: DBUser
    guild: GuildSettings
    reason: str
    end_time: datetime
