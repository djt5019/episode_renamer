PRAGMA foreign_keys = ON;

CREATE TABLE shows (
    sid INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    time TIMESTAMP
);

CREATE TABLE episodes (
    eid INTEGER PRIMARY KEY,
    sid INTEGER NOT NULL,
    eptitle TEXT NOT NULL,
    season INTEGER NOT NULL,
    showNumber INTEGER NOT NULL,
    FOREIGN KEY(sid) REFERENCES shows(sid)
);

CREATE TABLE specials{
	mid INTEGER PRIMARY KEY,
	sid, INTEGER NOT NULL,
	title TEXT NOT NULL,
	showNumber INTEGER NOT NULL,
	type TEXT NOT NULL,
	FOREIGN KEY(sid) REFERENCES shows(sid)
};
