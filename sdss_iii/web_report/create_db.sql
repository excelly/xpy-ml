CREATE TABLE object_info (
       pmf BIGINT PRIMARY KEY,
       sdss_id TEXT,
       spec_cln INTEGER,
       cla TEXT,
       subcla TEXT,
       z REAL,
       ra REAL,
       decl REAL,
       stamp INTEGER,
       mjd INTEGER
);

CREATE TABLE object_score (
       pmf BIGINT,
       run_id INTEGER,
       score REAL,
       rank INTEGER
);

-- index will be create by python scripts dynamically

CREATE TABLE object_label (
       pmf BIGINT PRIMARY KEY,
       rating INTEGER,
       comment TEXT,
       author INTEGER,
       last_update TEXT
);

CREATE INDEX IDX_SCORE_LABEL
ON object_label (pmf);

CREATE INDEX IDX_SCORE_RATING
ON object_label (rating);
