CREATE TABLE object_info (
       pmf BIGINT PRIMARY KEY,
       sdss_id TEXT,
       spec_cln INTEGER,
       cla TEXT,
       subcla TEXT,
       z REAL,
       ra REAL,
       decl REAL,
       stamp INTEGER
       
);

CREATE INDEX IDX_INFO_CLASS 
ON object_info (spec_cln);

CREATE INDEX IDX_INFO_PMF_STAMP
ON object_info (pmf, stamp);

CREATE TABLE object_score (
       pmf BIGINT PRIMARY KEY,
       run_id INTEGER,
       score REAL,
       rank INTEGER
);

CREATE INDEX IDX_SCORE_RID_SCORE
ON object_score (run_id, score);

CREATE TABLE object_label (
       pmf BIGINT,
       rating INTEGER,
       comment TEXT,
       author TEXT,
       last_update TEXT,
       likes INTEGER,
       dislikes INTEGER
);

CREATE INDEX IDX_LABEL_PA
ON object_label (pmf, author);

CREATE INDEX IDX_LABEL_RATING
ON object_label (rating);
