CREATE TABLE users (
       user_id INTEGER PRIMARY KEY,
       email TEXT NO NULL UNIQUE,
       password TEXT,
       nick_name TEXT,
       real_name TEXT,
       institute TEXT
);
