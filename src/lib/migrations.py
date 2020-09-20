#!/usr/bin/env python3

import os
import sys
import psycopg2
import subprocess
from packaging import version
from lib.logger import create_logger

'''
    SQL migration DDL's are copied from upstream powerdns
    https://github.com/PowerDNS/pdns/tree/master/modules/gpgsqlbackend
'''

# Create logger
log = create_logger(name='migrations')


def parse_sql_schema_filename(filename):
    old = version.parse(filename.split('_')[0])
    new = version.parse(filename.split('_')[2])
    return old, new


class PSQL:
    # TODO: Implement config file. Grab all settings needed from config file
    def __init__(self, config, silent=False):
        self.silent = silent
        self.pdns_pgsql_dbname = config['PDNS_PGSQL_DBNAME']
        self.pdns_pgsql_user = config['PDNS_PGSQL_USER']
        self.pdns_pgsql_password = config['PDNS_PGSQL_PASSWORD']
        self.pdns_pgsql_host = config['PDNS_PGSQL_HOST']
        self.pdns_pgsql_port = config['PDNS_PGSQL_PORT']

        self.conn_obj = None
        self.cursor_obj = None

    def connection(self):
        try:
            conn = psycopg2.connect(f"host={self.pdns_pgsql_host} \
                                            port={self.pdns_pgsql_port} \
                                            dbname={self.pdns_pgsql_dbname} \
                                            user={self.pdns_pgsql_user} \
                                            password={self.pdns_pgsql_password}")
            if not self.silent:
                log.debug(f"Connected to database [{self.pdns_pgsql_dbname}]")
            return conn
        except Exception as error:
            log.error(f"Unable to connect to the database [{self.pdns_pgsql_dbname}]")
            log.error(error)

    def cursor_create(self):
        self.conn_obj = self.connection()
        self.cursor_obj = self.conn_obj.cursor()
        return self.cursor_obj

    def close_all(self):
        try:
            self.cursor_obj.close()
            if not self.silent:
                log.debug("Cursor closed")
        except Exception as error:
            log.error(error)
        try:
            self.conn_obj.close()
            if not self.silent:
                log.debug("Connection Closed")
        except Exception as error:
            log.error(error)

    def commit(self):
        log.debug(f"Committing SQL query [{self.cursor_obj.query}]")
        self.conn_obj.commit()

    def rollback(self):
        log.debug(f"Rolling back SQL query [{self.cursor_obj.query}]")
        self.conn_obj.rollback()


class Migration:
    def __init__(self, config):
        self.config = config

    def single_query(self, query, silent):
        """
            Run a simple single read query.
        """
        conn = None
        try:
            conn = PSQL(self.config, silent)
            cursor = conn.cursor_create()
            cursor.execute(query)
            record = cursor.fetchone()[0]
            return record

        except (Exception, psycopg2.Error) as error:
            raise error

        finally:
            if conn is not None:
                conn.close_all()

    def get_pdns_db_version(self):
        """
            Grab the PowerDNS version stored in pdns_meta
        """
        try:
            record = self.single_query("select db_version from pdns_meta", True)
            return record

        except TypeError as error:
            log.error(error)
            return None

    def bump_pdns_db_version(self, new_version, old_version):
        """
            Update the PowerDNS version stored in pdns_meta. Also store the previous version.
        """
        conn = None
        try:
            conn = PSQL(self.config)
            cursor = conn.cursor_create()
            query = f"update pdns_meta set db_version='{new_version}', db_version_previous='{old_version}' where db_version='{old_version}'"
            cursor.execute(query)
            conn.commit()

        except (Exception, psycopg2.DatabaseError) as error:
            conn.rollback()
            raise (f"Was unable to bump the version number to the latest! [{old_version} -> {new_version}]")
            raise error

        finally:
            if conn is not None:
                conn.close_all()

    def run_migration(self, file_path, old_version, new_version):
        """
            Migrate DB to new version
        """
        conn = None
        try:
            conn = PSQL(self.config)
            with conn.cursor_create() as cursor:
                cursor.execute(open(file_path, "r").read())
            conn.commit()
            self.bump_pdns_db_version(new_version, old_version)
            log.info(f"Upgrade success!")

        except (Exception, psycopg2.DatabaseError) as error:
            conn.rollback()
            raise error

        finally:
            if conn is not None:
                conn.close_all()

    def execute_sql_schema(self, file_path):
        """
            Install fresh DB
        """
        conn = None
        try:
            conn = PSQL(self.config)
            with conn.cursor_create() as cursor:
                cursor.execute(open(file_path, "r").read())
            conn.commit()
            log.info(f"SQL success!")

        except (Exception, psycopg2.DatabaseError) as error:
            conn.rollback()
            raise error

        finally:
            if conn is not None:
                conn.close_all()


def run_migrations(mig, sql_schemas_path):
    try:
        # Grab PowerDNS version from env. DO NOT OVERWRITE THIS ENV VARIABLE!
        pdns_version = os.environ['POWERDNS_VERSION']
    except Exception as error:
        log.error(f"Unable to get or missing environment variable.")
        log.error(error)
        sys.exit(1)

    if pdns_version is None or pdns_version == "":
        log.error("Missing value from PowerDNS. Should be something like '4.1.0'")
        log.info("Cannot continue... Killing!")
        sys.exit(1)
    else:
        version_pdns = version.parse(pdns_version)
        log.debug(f"PowerDNS version: {pdns_version}")

    pdns_db_version = mig.get_pdns_db_version()
    if pdns_db_version is None or pdns_db_version == "":
        log.error("Missing value in column db_version in table pdns_meta. Should be something like '4.1.0'")
        log.info("Cannot continue... Killing!")
        sys.exit(1)
    else:
        version_pdns_db = version.parse(pdns_db_version)
        log.debug(f"Database version: {pdns_db_version}")

    if (version_pdns.major == version_pdns_db.major) and (version_pdns.minor > version_pdns_db.minor):
        log.info("Found version mismatch. Attempting upgrade...")
        log.debug("Walking sql_upgrade_scripts")
        for dir_path, subdir_list, file_list in os.walk(sql_schemas_path):
            for filename in file_list:
                schema_old, schema_new = parse_sql_schema_filename(filename)
                # Compare the major & minor versions of the running instances and the sql upgrade scripts
                # located at "sql_upgrade_scripts".
                if (version_pdns_db.minor == schema_old.minor) and \
                        (version_pdns.minor == schema_new.minor) and \
                        (version_pdns.major == schema_old.major):
                    log.debug(f"Found match: {filename}")
                    try:
                        full_path = os.path.join(dir_path, filename)
                        log.info(f"Upgrading from {schema_old} to {schema_new}")
                        # TODO: Implement better error handling
                        mig.run_migration(full_path, schema_old, schema_new)
                    except Exception as error:
                        log.error(error)
                else:
                    log.debug(f"sql_upgrade_script: {filename}")
    else:
        log.info("No upgrade needed... Continuing")

