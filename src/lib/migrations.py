#!/usr/bin/env python3

import os
import sys
import psycopg2
import subprocess
import logging
from packaging import version
from lib.config import Config

'''
    SQL migration DDL's are copied from upstream powerdns
    https://github.com/PowerDNS/pdns/tree/master/modules/gpgsqlbackend
'''

logger_name = f'{Config.logger_name}.migrations'
log = logging.getLogger(logger_name)


def parse_sql_schema_filename(filename):
    old = version.parse(filename.split('_')[0])
    new = version.parse(filename.split('_')[2])
    return old, new


class PSQL:
    # TODO: Implement config file. Grab all settings needed from config file
    def __init__(self, config, silent=False):
        self._logger = logging.getLogger(f'{logger_name}.{self.__class__.__name__}')
        self.silent = silent
        self.pdns_pgsql_dbname = config.pgsql_dbname
        self.pdns_pgsql_user = config.pgsql_user
        self.pdns_pgsql_password = config.pgsql_password
        self.pdns_pgsql_host = config.pgsql_host
        self.pdns_pgsql_port = config.pgsql_port

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
                self._logger.debug(f"Connected to database [{self.pdns_pgsql_dbname}]")
            return conn
        except Exception as error:
            self._logger.error(f"Unable to connect to the database [{self.pdns_pgsql_dbname}]")
            self._logger.error(error)

    def cursor_create(self):
        self.conn_obj = self.connection()
        self.cursor_obj = self.conn_obj.cursor()
        return self.cursor_obj

    def close_all(self):
        try:
            self.cursor_obj.close()
            if not self.silent:
                self._logger.debug("Cursor closed")
        except Exception as error:
            self._logger.error(error)
        try:
            self.conn_obj.close()
            if not self.silent:
                self._logger.debug("Connection Closed")
        except Exception as error:
            self._logger.error(error)

    def commit(self):
        self._logger.debug(f"Committing SQL query [{self.cursor_obj.query}]")
        self.conn_obj.commit()

    def rollback(self):
        self._logger.debug(f"Rolling back SQL query [{self.cursor_obj.query}]")
        self.conn_obj.rollback()


class Migration:
    def __init__(self, config):
        self.config = config
        #self._logger = logging.getLogger(f'{logger_name}.{self.__class__.__name__}')
        self._logger = log

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
            if record is None or record == "":
                self._logger.error("Missing value in column db_version in table pdns_meta. Should be something like '4.1.0'")
                sys.exit(1)
            else:
                pdns_db_version = version.parse(record)
                self._logger.debug(f"Database version: {record}")
                return pdns_db_version

        except TypeError as error:
            self._logger.error(error)
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
            self._logger.debug(f'Bumping DB version: [{old_version} -> {new_version}]')
            cursor.execute(query)
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            conn.rollback()
            self._logger.error(f"Was unable to bump the version number to the latest! [{old_version} -> {new_version}]")
            raise (f"Was unable to bump the version number to the latest! [{old_version} -> {new_version}]")
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
            self._logger.info(f"Upgrade success!")
        except (Exception, psycopg2.DatabaseError) as error:
            conn.rollback()
            self._logger.error(f'Unable to migrate: File: {file_path}')
            raise error

        finally:
            if conn is not None:
                conn.close_all()

    def execute_sql_schema(self, file_path):
        conn = None
        try:
            conn = PSQL(self.config)
            with conn.cursor_create() as cursor:
                cursor.execute(open(file_path, "r").read())
            conn.commit()
            #self._logger.info(f"SQL success!")

        except (Exception, psycopg2.DatabaseError) as error:
            conn.rollback()
            raise error

        finally:
            if conn is not None:
                conn.close_all()


def convert_version_name(name):
    result = None
    name = str(name)
    if len(name) == 2:
        # Good to continue
        result = f'{name[0]}.{name[1]}.0'
    return result


def run_migrations(mig, sql_schemas_path, pdns_version_raw):
    if pdns_version_raw is None or pdns_version_raw == "":
        log.error("Missing value from PowerDNS. Should be something like '4.1.0'")
        log.info("Cannot continue... Killing!")
        sys.exit(1)
    else:
        pdns_version = version.parse(pdns_version_raw)
        log.debug(f"PowerDNS version: {pdns_version_raw}")

    pdns_db_version = mig.get_pdns_db_version()

    if pdns_version.major == pdns_db_version.major and pdns_version.minor > pdns_db_version.minor:
        log.info("Found new version. Atempting upgrade!")
        log.debug(f"Walking {sql_schemas_path}")
        for dir_path, subdir_list, file_list in os.walk(sql_schemas_path):
            for filename in file_list:
                schema_old, schema_new = parse_sql_schema_filename(filename)
                log.debug(f'Old schema version: {schema_old}')
                log.debug(f'New schema version: {schema_new}')

                pdns_db_version = mig.get_pdns_db_version()
                if schema_old.major == pdns_db_version.major and schema_old.minor == pdns_db_version.minor and pdns_version.major == schema_new.major and pdns_version.minor >= schema_new.minor:
                    log.info(f"Found match: {filename}")
                    try:
                        full_path = os.path.join(dir_path, filename)
                        log.info(f"Upgrading from {schema_old} to {schema_new}")
                        # TODO: Implement better error handling
                        log.debug('RUNNING MIGRATION!')
                        mig.run_migration(full_path, schema_old, schema_new)
                    except Exception as error:
                        log.error(error)
                else:
                    log.debug(f"Skipping script: {filename}")
    else:
        log.info("No upgrade needed... Continuing")

