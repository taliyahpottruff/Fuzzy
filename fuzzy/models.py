from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DurationType(Enum):
    DAYS = 1
    MONTHS = 2
    YEARS = 3


class InfractionType(Enum):
    WARN = 1
    MUTE = 2
    BAN = 3


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


@dataclass()
class Mute(object):
    infraction: Infraction
    end_time: datetime


@dataclass()
class Lock(object):
    channel_id: int
    moderator: DBUser
    guild: GuildSettings
    reason: str
    end_time: datetime
