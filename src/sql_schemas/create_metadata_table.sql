-- Drop table

-- DROP TABLE public.pdns_meta;

CREATE TABLE public.pdns_meta (
	--id SERIAL,
	db_version varchar(10) NOT NULL,
	db_version_previous varchar(10) NOT NULL,
	CONSTRAINT pdns_meta_pkey PRIMARY KEY (db_version, db_version_previous)
);

-- Insert defaults
INSERT INTO public.pdns_meta VALUES ('4.1.0', '0') ON CONFLICT DO NOTHING;

-- Permissions

ALTER TABLE public.pdns_meta OWNER TO pdns;
GRANT ALL ON TABLE public.pdns_meta TO pdns;
