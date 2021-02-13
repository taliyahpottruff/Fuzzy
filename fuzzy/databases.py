import sqlite3
from datetime import datetime, timedelta
from typing import List, TextIO

from fuzzy.interfaces import (
    IInfractions,
    IDatabase,
    IGuilds,
    IPardons,
    IMutes,
    ILocks,
    IPublishedMessages,
)
from fuzzy.models import (
    Infraction,
    InfractionType,
    PublishType,
    PublishedMessage,
    DBUser,
    GuildSettings,
    Pardon,
    Mute,
    Lock,
)


class Database(IDatabase):
    def __init__(self, config, schema_file: TextIO):
        super().__init__(config, schema_file)


class Infractions(IInfractions):
    def __init__(self, conn: sqlite3.Connection, db: IDatabase):
        self.conn = conn
        self.db = db

    def find_by_id(self, infraction_id: int, guild_id: int) -> Infraction:
        infraction = self.conn.execute(
            "SELECT * FROM infractions WHERE oid=:id AND guild_id=:guild_id",
            {"id": infraction_id, "guild_id": guild_id},
        ).fetchone()
        if not infraction:
            raise ValueError("No infraction with that ID on this server.")

        return Infraction(
            infraction["oid"],
            DBUser(infraction["user_id"], infraction["user_name"]),
            DBUser(infraction["moderator_id"], infraction["moderator_name"]),
            self.db.guilds.find_by_id(guild_id),
            infraction["reason"],
            infraction["infraction_on"],
            InfractionType(infraction["infraction_type"]),
            self.db.pardons.find_by_id(infraction_id),
            self.db.published_messages.find_by_id_and_type(
                infraction_id, PublishType.BAN
            ),
            self.db.published_messages.find_by_id_and_type(
                infraction_id, PublishType.UNBAN
            ),
        )

    def save(self, infraction: Infraction) -> Infraction:
        if infraction.id:
            retrieved_infraction = self.find_by_id(infraction.id, infraction.guild.id)
            self.conn.execute(
                "UPDATE infractions SET reason=:reason WHERE oid=:id",
                {"reason": infraction.reason, "id": infraction.id},
            )
            self.conn.commit()
            return retrieved_infraction
        else:
            values = (
                infraction.user.id,
                infraction.user.name,
                infraction.moderator.id,
                infraction.moderator.name,
                infraction.guild,
                infraction.reason,
                infraction.infraction_on,
                infraction.infraction_type,
            )
            sql = """INSERT INTO infractions (user_id, user_name, moderator_id, moderator_name, guild_id, reason, 
            infraction_on, infraction_type) VALUES(?,?,?,?,?,?,?,?)"""
            try:
                self.conn.execute(sql, values)
                self.conn.commit()
            except sqlite3.DatabaseError:
                pass
            # noinspection PyTypeChecker
            return self.find_by_id(infraction.id, infraction.guild)

    def delete(self, infraction_id: int) -> None:
        self.conn.execute(
            "DELETE FROM infractions WHERE oid=:id", {"id": infraction_id}
        )
        self.conn.commit()

    def find_recent_ban_by_id(self, user_id, guild_id) -> Infraction:
        past_hour = datetime.utcnow() - timedelta(hours=1)
        infraction = None
        try:
            infraction = self.conn.execute(
                "SELECT * FROM infractions WHERE DATETIME(infraction_on)<:timestamp AND user_id=:user_id "
                "AND guild_id=:guild_id",
                {"timestamp": past_hour, "user_id": user_id, "guild_id": guild_id},
            ).fetchone()
        except sqlite3.DatabaseError:
            pass

        return (
            Infraction(
                infraction["oid"],
                DBUser(infraction["user_id"], infraction["user_name"]),
                DBUser(infraction["moderator_id"], infraction["moderator_name"]),
                self.db.guilds.find_by_id(guild_id),
                infraction["reason"],
                infraction["infraction_on"],
                InfractionType(infraction["infraction_type"]),
                self.db.pardons.find_by_id(infraction["oid"]),
                self.db.published_messages.find_by_id_and_type(
                    infraction["oid"], PublishType.BAN
                ),
                self.db.published_messages.find_by_id_and_type(
                    infraction["oid"], PublishType.UNBAN
                ),
            )
            if infraction
            else None
        )


class Pardons(IPardons):
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def find_by_id(self, infraction_id: int) -> Pardon:
        pardon = None
        try:
            pardon = self.conn.execute(
                "SELECT * FROM pardons WHERE infraction_id=:infraction_id",
                {"infraction_id": infraction_id},
            ).fetchone()
        except sqlite3.DatabaseError:
            pass
        finally:
            return (
                Pardon(
                    pardon["infraction_id"],
                    DBUser(pardon["moderator_id"], pardon["moderator_name"]),
                    pardon["pardon_on"],
                    pardon["reason"],
                )
                if pardon
                else None
            )

    def save(self, pardon: Pardon) -> Pardon:
        pardon = self.conn.execute(
            "SELECT * FROM pardons WHERE infraction_id=:infraction_id",
            {"infraction_id": pardon.infraction_id},
        ).fetchone()
        if pardon:
            self.conn.execute(
                "UPDATE pardons SET reason=:reason WHERE infraction_id=:infraction_id",
                {"reason": pardon.reason, "infraction_id": pardon.infraction_id},
            )
            self.conn.commit()
        else:
            values = (
                pardon.infraction_id,
                pardon.moderator.id,
                pardon.moderator.name,
                pardon.pardon_on,
                pardon.reason,
            )
            sql = """INSERT INTO pardons (infraction_id, moderator_id, moderator_name, pardon_on, reason)
            Values(?,?,?,?,?)"""
            self.conn.execute(sql, values)
            self.conn.commit()

        return self.find_by_id(pardon.infraction_id)

    def delete(self, infraction_id: int) -> None:
        self.conn.execute(
            "DELETE FROM pardons WHERE infraction_id=:id", {"id": infraction_id}
        )
        self.conn.commit()


class Mutes(IMutes):
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def find_by_id(self, infraction_id: int) -> Mute:
        mute = None
        try:
            mute = self.conn.execute(
                "SELECT * FROM mutes WHERE infraction_id=:infraction_id",
                {"infraction_id": infraction_id},
            ).fetchone()
        except sqlite3.DatabaseError:
            pass
        finally:
            return (
                Mute(
                    mute["infraction_id"],
                    mute["end_time"],
                    DBUser(mute["user_id"], mute["user_name"]),
                )
                if mute
                else None
            )

    def find_expired_mutes(self) -> List[Mute]:
        mutes = None
        try:
            mutes = self.conn.execute(
                "SELECT * FROM mutes WHERE DATETIME(end_time) < :time",
                {"time": datetime.utcnow()},
            ).fetchall()
        except sqlite3.DatabaseError:
            pass
        finally:
            objectified_mutes = []
            for mute in mutes:
                objectified_mutes.append(
                    Mute(
                        mute["infraction_id"],
                        mute["end_time"],
                        DBUser(mute["user_id"], mute["user_name"]),
                    )
                )
            return objectified_mutes

    def save(self, mute: Mute) -> Mute:
        values = (mute.infraction.id, mute.end_time, mute.user.id, mute.user.name)
        sql = """INSERT INTO mutes (infraction_id, end_time, user_id, user_name) VALUES(?,?,?,?)"""
        try:
            self.conn.execute(sql, values)
            self.conn.commit()
        except sqlite3.DatabaseError:
            pass
        finally:
            return mute

    def delete(self, infraction_id: int) -> None:
        self.conn.execute(
            "DELETE FROM mutes WHERE infraction_id=:id", {"id": infraction_id}
        )
        self.conn.commit()

    def find_active_mute(self, user_id, guild_id) -> Mute:
        mute = None
        try:
            mute = self.conn.execute(
                "SELECT * FROM mutes WHERE DATETIME(end_time) > :time AND user_id=:user_id",
                {"time": datetime.utcnow(), "user_id": user_id},
            ).fetchone()
        except sqlite3.DatabaseError:
            pass
        finally:
            return (
                Mute(
                    mute["infraction_id"],
                    mute["end_time"],
                    DBUser(mute["user_id"], mute["user_name"]),
                )
                if mute
                else None
            )


class Guilds(IGuilds):
    def __init__(self, conn: sqlite3.Connection, db: IDatabase):
        self.conn = conn
        self.db = db

    def find_by_id(self, guild_id: int) -> GuildSettings:
        guild = self.conn.execute("SELECT * FROM guilds WHERE id=:id", {"id": guild_id})

    def save(self, guild: GuildSettings) -> GuildSettings:
        pass

    def delete(self, guild_id: int) -> None:
        pass


class Locks(ILocks):
    def __init__(self, conn: sqlite3.Connection, db: IDatabase):
        self.conn = conn
        self.db = db

    def find_by_id(self, channel_id: int) -> Lock:
        pass

    def find_expired_locks(self) -> List[Lock]:
        pass

    def save(self, mute: Lock) -> Lock:
        pass

    def delete(self, channel_id: int) -> None:
        pass


class PublishedMessages(IPublishedMessages):
    def __init__(self, conn: sqlite3.Connection, db: IDatabase):
        self.conn = conn
        self.db = db

    def find_by_id_and_type(
        self, infraction_id: int, publish_type: PublishType
    ) -> PublishedMessage:
        publish = self.conn.execute(
            "SELECT * FROM published_messages WHERE infraction_id=:infraction_id "
            "AND publish_type=:publish_type",
            {"infraction_id": infraction_id, "publish_type": publish_type},
        ).fetchone()
        return (
            PublishedMessage(
                publish["infraction_id"],
                publish["message_id"],
                PublishType(publish.publishtype),
            )
            if publish
            else None
        )

    def save(self, published_ban: PublishedMessage) -> PublishedMessage:
        pass

    def delete(self, guild_id: int) -> None:
        pass
