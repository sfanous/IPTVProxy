BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "settings" (
	"name"	TEXT NOT NULL,
	"value"	TEXT NOT NULL,
	PRIMARY KEY("name")
);
CREATE TABLE IF NOT EXISTS "program_temp" (
	"channel_id"	TEXT NOT NULL,
	"provider"	TEXT NOT NULL,
	"start_date_time_in_utc"	TEXT NOT NULL,
	"end_date_time_in_utc"	TEXT NOT NULL,
	"title"	TEXT NOT NULL,
	"sub_title"	TEXT NOT NULL,
	"description"	TEXT NOT NULL,
	FOREIGN KEY("channel_id") REFERENCES "channel_temp"("id") ON DELETE CASCADE ON UPDATE CASCADE,
	PRIMARY KEY("channel_id","provider","start_date_time_in_utc","end_date_time_in_utc")
);
CREATE TABLE IF NOT EXISTS "program" (
	"channel_id"	TEXT NOT NULL,
	"provider"	TEXT NOT NULL,
	"start_date_time_in_utc"	TEXT NOT NULL,
	"end_date_time_in_utc"	TEXT NOT NULL,
	"title"	TEXT NOT NULL,
	"sub_title"	TEXT NOT NULL,
	"description"	TEXT NOT NULL,
	FOREIGN KEY("channel_id") REFERENCES "channel"("id") ON DELETE CASCADE ON UPDATE CASCADE,
	PRIMARY KEY("channel_id","provider","start_date_time_in_utc","end_date_time_in_utc")
);
CREATE TABLE IF NOT EXISTS "channel_temp" (
	"id"	TEXT NOT NULL,
	"provider"	TEXT NOT NULL,
	"number"	TEXT NOT NULL,
	"name"	TEXT NOT NULL,
	"icon_data_uri"	BLOB NOT NULL,
	"icon_url"	TEXT NOT NULL,
	"group"	TEXT NOT NULL,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "channel" (
	"id"	TEXT NOT NULL,
	"provider"	TEXT NOT NULL,
	"number"	TEXT NOT NULL,
	"name"	TEXT NOT NULL,
	"icon_data_uri"	BLOB NOT NULL,
	"icon_url"	TEXT NOT NULL,
	"group"	TEXT NOT NULL,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "http_session" (
	"id"	TEXT NOT NULL,
	"client_ip_address"	TEXT NOT NULL,
	"user_agent"	TEXT NOT NULL,
	"last_access_date_time_in_utc"	TEXT NOT NULL,
	"expiry_date_time_in_utc"	TEXT NOT NULL,
	PRIMARY KEY("id","client_ip_address","user_agent","last_access_date_time_in_utc","expiry_date_time_in_utc")
);
CREATE TABLE IF NOT EXISTS "recording" (
	"id"	TEXT NOT NULL,
	"provider"	TEXT NOT NULL,
	"channel_number"	TEXT NOT NULL,
	"channel_name"	TEXT NOT NULL,
	"program_title"	TEXT NOT NULL,
	"start_date_time_in_utc"	TEXT NOT NULL,
	"end_date_time_in_utc"	TEXT NOT NULL,
	"status"	TEXT NOT NULL,
	PRIMARY KEY("provider","channel_number","start_date_time_in_utc","end_date_time_in_utc")
);
COMMIT;
