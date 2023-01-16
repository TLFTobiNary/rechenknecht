BEGIN TRANSACTION;
DROP TABLE IF EXISTS "items";
CREATE TABLE IF NOT EXISTS "items" (
        "id"    INTEGER PRIMARY KEY AUTOINCREMENT,
        "description"      TEXT NOT NULL,
	"shopid" INTEGER NOT NULL,
        "price"     INTEGER  NOT NULL
);

DROP TABLE IF EXISTS "shops";
CREATE TABLE IF NOT EXISTS "shops" (
	"id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"name" TEXT UNIQUE NOT NULL
	);

drop table if exists "runs";
create table if not exists "runs" (
	"id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"shopid" INTEGER NOT NULL,
	"date" DATE NOT NULL,
	"paid" BOOL DEFAULT False,
	foreign key(shopid) references shops(id)
	);

DROP TABLE IF EXISTS "purchases";
CREATE TABLE IF NOT EXISTS "purchases" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"runid" INTEGER NOT NULL,
	"itemid" INTEGER NOT NULL,
	"price" INTEGER NOT NULL,
	"userid" INTEGER NOT NULL,
	"poolid" INTEGER NOT NULL,
	foreign key(runid) references runs(id),
	foreign key(itemid) references items(id),
	foreign key(userid) references users(id),
	foreign key(poolid) references pools(id)
	);

DROP TABLE IF EXISTS "users";
CREATE TABLE IF NOT EXISTS "users" (
	"id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"username" TEXT UNIQUE NOT NULL,
	"password" TEXT NOT NULL,
	"privileges" INTEGER DEFAULT 0,
	"disabled" BOOL DEFAULT False,
	"darkmode" BOOL Default False
	);
drop TABLE IF EXISTS "pools";
create table if not exists "pools" (
	"id" integer primary key autoincrement,
	"description" TEXT NOT NULL
	);

DROP TABLE IF EXISTS "poolsusers";
create table if not exists "poolsusers" (
	id integer primary key autoincrement,
	"user" integer not null,
	"pool" integer not null,
	foreign key(user) references users(id),
	foreign key(pool) references pools(id)
	);

insert into "users" values (0, "admin", "pbkdf2:sha256:150000$dgMqt2Ib$5222f22c1d876b8a01f8549723b1fb9e263394f1c7785cef3eaa0e7f99ed2dd7", 1, FALSE, FALSE);


insert into "shops" values (0, "Demo Shop");

insert into "pools" values(0, "admin");
insert into "poolsusers" values(0, 0, 0);


INSERT INTO items VALUES(0,'Demo Product',0,99);




COMMIT;

