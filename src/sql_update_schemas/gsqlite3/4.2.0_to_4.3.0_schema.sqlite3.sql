BEGIN TRANSACTION;
  CREATE TABLE cryptokeys_temp (
    id                  INTEGER PRIMARY KEY,
    domain_id           INT NOT NULL,
    flags               INT NOT NULL,
    active              BOOL,
    published           BOOL DEFAULT 1,
    content             TEXT,
    FOREIGN KEY(domain_id) REFERENCES domains(id) ON DELETE CASCADE ON UPDATE CASCADE
  );

  INSERT INTO cryptokeys_temp SELECT id,domain_id,flags,active,1,content FROM cryptokeys;
  DROP TABLE cryptokeys;
  ALTER TABLE cryptokeys_temp RENAME TO cryptokeys;

  CREATE INDEX domainidindex ON cryptokeys(domain_id);
COMMIT;

-- CREATE INDEX records_lookup_idx ON records(name, type);
-- CREATE INDEX records_lookup_id_idx ON records(domain_id, name, type);
-- CREATE INDEX records_order_idx ON records(domain_id, ordername);

-- DROP INDEX IF EXISTS rec_name_index;
-- DROP INDEX IF EXISTS nametype_index;
-- DROP INDEX IF EXISTS domain_id;
-- DROP INDEX IF EXISTS orderindex;

-- CREATE INDEX comments_idx ON comments(domain_id, name, type);

-- DROP INDEX IF EXISTS comments_domain_id_index;
-- DROP INDEX IF EXISTS comments_nametype_index;

-- ANALYZE;