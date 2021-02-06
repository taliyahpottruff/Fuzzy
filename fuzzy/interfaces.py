import sqlite3
from abc import ABC, abstractmethod
from typing import TextIO

from fuzzy.models import *


class IInfractions(ABC):

    @abstractmethod
    def find_by_id(self, infraction_id: int) -> Infraction:
        pass

    @abstractmethod
    def save(self, infraction: Infraction) -> Infraction:
        pass

    @abstractmethod
    def delete(self, infraction_id: int) -> None:
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
    def find_expired_mutes(self) -> Mute:
        pass

    @abstractmethod
    def save(self, mute: Mute) -> Mute:
        pass

    @abstractmethod
    def delete(self, infraction_id: int) -> None:
        pass


class IGuilds(ABC):

    @abstractmethod
    def find_by_id(self, guild_id: int) -> GuildSettings:
        pass

    @abstractmethod
    def save(self, pardon: GuildSettings) -> GuildSettings:
        pass

    @abstractmethod
    def delete(self, guild_id: int) -> None:
        pass


class ILocks(ABC):

    @abstractmethod
    def find_by_id(self, channel_id: int) -> Lock:
        pass

    @abstractmethod
    def find_expired_locks(self) -> Lock:
        pass

    @abstractmethod
    def save(self, mute: Lock) -> Lock:
        pass

    @abstractmethod
    def delete(self, channel_id: int) -> None:
        pass


class IDatabase(ABC):

    @abstractmethod
    def __init__(self , config, schema_file: TextIO):
        self.conn: sqlite3.Connection
        self.infractions: IInfractions
        self.pardons: IPardons
        self.mutes: IMutes
        self.guilds: IGuilds
        self.locks: ILocks

