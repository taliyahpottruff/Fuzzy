import sqlite3
from abc import ABC, abstractmethod
from typing import TextIO, List

from fuzzy.models import *


class IInfractions(ABC):
    @abstractmethod
    def find_by_id(self, infraction_id: int, guild_id: int) -> Infraction:
        pass

    @abstractmethod
    def save(self, infraction: Infraction) -> Infraction:
        pass

    @abstractmethod
    def delete(self, infraction_id: int) -> None:
        pass

    @abstractmethod
    def find_recent_ban_by_id(self, user_id, guild_id) -> Infraction:
        pass


class IPardons(ABC):
    @abstractmethod
    def find_by_id(self, infraction_id: int) -> Pardon:
        pass

    @abstractmethod
    def save(self, pardon: Pardon) -> Pardon:
        pass

    @abstractmethod
    def delete(self, infraction_id: int) -> None:
        pass


class IMutes(ABC):
    @abstractmethod
    def find_by_id(self, infraction_id: int) -> Mute:
        pass

    @abstractmethod
    def find_expired_mutes(self) -> List[Mute]:
        pass

    @abstractmethod
    def save(self, mute: Mute) -> Mute:
        pass

    @abstractmethod
    def delete(self, infraction_id: int) -> None:
        pass

    @abstractmethod
    def find_active_mute(self, user_id, guild_id) -> Mute:
        pass


class IGuilds(ABC):
    @abstractmethod
    def find_by_id(self, guild_id: int) -> GuildSettings:
        pass

    @abstractmethod
    def save(self, guild: GuildSettings) -> GuildSettings:
        pass

    @abstractmethod
    def delete(self, guild_id: int) -> None:
        pass


class ILocks(ABC):
    @abstractmethod
    def find_by_id(self, channel_id: int) -> Lock:
        pass

    @abstractmethod
    def find_expired_locks(self) -> List[Lock]:
        pass

    @abstractmethod
    def save(self, mute: Lock) -> Lock:
        pass

    @abstractmethod
    def delete(self, channel_id: int) -> None:
        pass


class IPublishedMessages(ABC):
    @abstractmethod
    def find_by_id_and_type(
        self, infraction_id: int, publish_type: PublishType
    ) -> PublishedMessage:
        pass

    @abstractmethod
    def save(self, published_ban: PublishedMessage) -> PublishedMessage:
        pass

    @abstractmethod
    def delete(self, guild_id: int) -> None:
        pass


class IDatabase(ABC):
    @abstractmethod
    def __init__(self, config, schema_file: TextIO):

        self.conn: sqlite3.Connection
        self.infractions: IInfractions = IInfractions()
        self.pardons: IPardons = IPardons()
        self.mutes: IMutes = IMutes()
        self.guilds: IGuilds = IGuilds()
        self.locks: ILocks = ILocks()
        self.published_messages: IPublishedMessages = IPublishedMessages()
