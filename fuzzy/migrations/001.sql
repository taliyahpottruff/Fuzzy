PRAGMA foreign_keys = ON;

-- Schema Version 1

-- Database Metadata
CREATE TABLE IF NOT EXISTS applied_migrations (
    number INTEGER PRIMARY KEY
);

-- Guild Application Settings
CREATE TABLE IF NOT EXISTS guilds (
    id              INTEGER PRIMARY KEY, -- Guild ID
    mod_log         INTEGER,
    public_log      INTEGER,
    duration_type   INTEGER CHECK(duration_type == 1 OR duration_type == 2 OR duration_type == 3), -- ENUM
    duration        INTEGER,
    mute_role       INTEGER
);

-- Saved Infractions
CREATE TABLE IF NOT EXISTS infractions (
    oid             INTEGER     PRIMARY KEY,
    user_id         INTEGER     NOT NULL,
    user_name       TEXT        NOT NULL,
    moderator_id    INTEGER     NOT NULL,
    moderator_name  TEXT        NOT NULL,
    guild_id        INTEGER     NOT NULL,
    reason          TEXT,
    infraction_on   timestamp   NOT NULL,
    infraction_type TEXT     NOT NULL CHECK(infraction_type == 1 OR infraction_type == 2 OR infraction_type == 3),

    FOREIGN KEY(guild_id) REFERENCES guilds(id)
);

-- Saved Pardons
CREATE TABLE IF NOT EXISTS pardons (
    infraction_id   INTEGER     NOT NULL,
    moderator_id    INTEGER     NOT NULL,
    moderator_name  TEXT        NOT NULL,
    pardon_on       timestamp   NOT NULL,
    reason          TEXT,

    FOREIGN KEY(infraction_id) REFERENCES infractions(oid)
);

-- SAVED MUTES
CREATE TABLE IF NOT EXISTS mutes (
    infraction_id   INTEGER     NOT NULL,
    end_time        timestamp   NOT NULL,
    user_id         INTEGER     NOT NULL,
    user_name       TEXT        NOT NULL,

    FOREIGN KEY(infraction_id) REFERENCES infractions(oid)
);

-- Published Messages
CREATE TABLE IF NOT EXISTS published_messages (
    infraction_id   INTEGER     NOT NULL,
    message_id      INTEGER     NOT NULL,
    publish_type    integer     NOT NULL CHECK(publish_type == 1 or publish_type == 2),

    FOREIGN KEY(infraction_id) REFERENCES infractions(oid)
);

-- Locked Channels
CREATE TABLE IF NOT EXISTS locks (
    channel_id      INTEGER     PRIMARY KEY,
    previous_value  INTEGER     CHECK(previous_value == 1 OR previous_value == 0) ,--Bool + Null
    moderator_id    INTEGER     NOT NULL,
    moderator_name  TEXT        NOT NULL,
    guild_id        INTEGER     NOT NULL,
    reason          TEXT,
    end_time        timestamp   NOT NULL,

    FOREIGN KEY(guild_id) REFERENCES guilds(id)
);

