from datetime import datetime
from enum import Enum


class GuildSettings(object):

    class DurationType(Enum):
        DAYS = 1
        MONTHS = 2
        YEARS = 3

    def __init__(self,
                 guild_id: int,
                 mod_log: int,
                 public_log: int,
                 duration_type: DurationType,
                 duration: int,
                 mute_role: int):
        self.id = guild_id
        self.mod_log = mod_log
        self.public_log = public_log
        self.duration_type = duration_type
        self.duration = duration
        self.mute_role = mute_role


class DBUser(object):
    def __init__(self, user_id: int, name: str):
        self.id = user_id
        self.name = name


class Infraction(object):

    class InfractionType(Enum):
        WARN = 1
        MUTE = 2
        BAN = 3

    def __init__(self,
                 user: DBUser,
                 moderator: DBUser,
                 guild: GuildSettings,
                 reason: str,
                 infraction_on: datetime,
                 infraction_type: InfractionType):

        self.id = None
        self.user = user
        self.moderator = moderator
        self.guild = guild
        self.reason = reason
        self.date = infraction_on
        self.type = infraction_type
        self.pardon = None


class Pardon(object):
    def __init__(self, infraction_id: int, moderator: DBUser, pardon_on: datetime):
        """Foreign Key Infraction.id"""
        self.id = infraction_id
        self.moderator = moderator
        self.pardon_on = pardon_on


class Mute(object):
    def __init__(self, infraction: Infraction, end_time: datetime):
        self.infraction = infraction
        self.end_time = end_time


class Lock(object):
    def __init__(self,
                 channel_id: int,
                 moderator: DBUser,
                 guild: GuildSettings,
                 reason: str,
                 end_time: datetime
                 ):
        self.id = channel_id
        self.moderator = moderator
        self.guild = guild
        self.reason = reason
        self.end_time = end_time

