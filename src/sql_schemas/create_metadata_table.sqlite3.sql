CREATE TABLE pdns_meta (
	db_version varchar(10) NOT NULL,
	db_version_previous varchar(10) NOT NULL,
	CONSTRAINT pdns_meta_pkey PRIMARY KEY (db_version, db_version_previous)
);

-- Insert defaults
INSERT INTO pdns_meta VALUES ('4.1.0', '0');