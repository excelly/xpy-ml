CREATE TABLE object_similarity (
       feature INTEGER,
       similarity_type INTEGER,
       spec_cln INTEGER,
       pmf1 BIGINT,
       pmf2 BIGINT,
       similarity REAL
);

CREATE INDEX IDX_FSC
ON object_similarity (feature, similarity_type, spec_cln);

CREATE INDEX IDX_FSP1
ON object_similarity (feature, similarity_type, pmf1);
