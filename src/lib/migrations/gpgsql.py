import os
import sys
import psycopg2
import logging
import time
from packaging import version

from lib.config import Config, parse_sql_schema_filename
from lib.logger import logger as log
'''
    SQL migration DLL's are copied from upstream powerdns
    https://github.com/PowerDNS/pdns/tree/master/modules/gpgsqlbackend
'''

log_name = f'{Config.logger_name}.gpgsql'
log = logging.getLogger(log_name)
sql_schema = os.path.join(Config.sql_schema_path, '4.1.0_schema.pgsql.sql')
create_metadata_table = os.path.join(Config.sql_schema_path,
                                     'create_metadata_table.pgsql.sql')


class DB:
    def __init__(self):
        self.log_name = f"{log_name}.{self.__class__.__name__}"
        self.log = logging.getLogger(self.log_name)

        self.conn_obj = None
        self.cursor_obj = None

    def connection(self):
        try:
            conn = psycopg2.connect(f"host={Config.gpgsql_host} \
                                      port={Config.gpgsql_port} \
                                      dbname={Config.gpgsql_dbname} \
                                      user={Config.gpgsql_user} \
                                      password={Config.gpgsql_password}")
            self.log.debug(
                f"Connected to database [DB: {Config.gpgsql_dbname}@{Config.gpgsql_host}:{Config.gpgsql_port}]"
            )
            return conn

        except (Exception, psycopg2.Error) as error:
            self.log.error(
                f"Unable to connect to the database [DB: {Config.gpgsql_dbname}@{Config.gpgsql_host}:{Config.gpgsql_port}]"
            )
            self.log.debug(error)
            sys.exit(1)

    def create_cursor(self):
        self.conn_obj = self.connection()
        self.cursor_obj = self.conn_obj.cursor()
        return self.cursor_obj

    def close_all(self):
        try:
            self.cursor_obj.close()
            self.log.debug("Cursor closed")
        except (Exception, psycopg2.Error) as error:
            self.log.error(error)
        try:
            self.conn_obj.close()
            self.log.debug("Connection Closed")
        except (Exception, psycopg2.Error) as error:
            self.log.error(error)

    def commit(self):
        self.log.debug(f"Committing SQL query [{self.cursor_obj}]")
        self.conn_obj.commit()

    def rollback(self):
        self.log.debug(f"Rolling back SQL query [{self.cursor_obj}]")
        self.conn_obj.rollback()


def execute_single_query(query):
    """
        Run a simple single read query.
    """
    conn = DB()
    try:
        cursor = conn.create_cursor()
        cursor.execute(query)
        record = cursor.fetchone()[0]
        return record

    except (Exception, psycopg2.Error) as error:
        log.error(error)
        sys.exit(1)

    finally:
        if conn is not None:
            conn.close_all()


def execute_sql_schema(file_path):
    conn = DB()
    try:
        with conn.create_cursor() as cursor:
            cursor.execute(open(file_path, "r").read())
        conn.commit()
        log.info(f'Committed schema to database: {file_path}')

    except (Exception, psycopg2.DatabaseError) as error:
        conn.rollback()
        log.error(error)
        sys.exit(1)

    finally:
        if conn is not None:
            conn.close_all()


def bump_pdns_db_version(new_version, old_version):
    """
        Update the PowerDNS version stored in pdns_meta. Also store the previous version.
    """
    conn = DB()
    try:
        cursor = conn.create_cursor()
        query = f"update pdns_meta set db_version='{new_version}', db_version_previous='{old_version}' where db_version='{old_version}'"
        log.debug(f'Bumping DB version: [{old_version} -> {new_version}]')
        cursor.execute(query)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        conn.rollback()
        log.error(
            f"Was unable to bump the version number to the latest! [{old_version} -> {new_version}]"
        )
        log.debug(error)
        sys.exit(1)
    finally:
        if conn is not None:
            conn.close_all()


def db_connect_check(user, password, host, port):
    conn = None
    try:
        conn_string = f"host={host} port={port} user={user} password={password} connect_timeout=1"
        conn = psycopg2.connect(conn_string)
        return True
    except:
        return False
    finally:
        if conn is not None:
            conn.close()


def wait_for_db(timeout=30):
    time_end = time.time() + timeout
    while db_connect_check(host=Config.gpgsql_host,
                           port=Config.gpgsql_port,
                           user=Config.gpgsql_user,
                           password=Config.gpgsql_password) is False:
        if time.time() > time_end:
            log.error('Could not connect to the database')
            sys.exit(1)
        log.info(
            f"Waiting for postgres at: {Config.gpgsql_host}:{Config.gpgsql_port}"
        )
        time.sleep(5)


def has_existing_data(table_name):
    """
        Query for table domains and records
        If they exist and has content return true
    """
    query = f"select exists(select * from information_schema.tables where table_name='{table_name}')"
    record = execute_single_query(query)
    return record


def get_pdns_db_version():
    """
        Grab the PowerDNS version stored in pdns_meta and exits the program if missing
    """
    record = execute_single_query("select db_version from pdns_meta")
    if record is None or record == "":
        log.error(
            "Missing value in column db_version in table pdns_meta. Should be something like '4.1.0'"
        )
    else:
        pdns_db_version = version.parse(record)
        log.debug(f"Database version: {record}")
        return pdns_db_version


def install():
    """
        Creates new DB if it does not exist. Also populates it with an empty schema if it does not exist
    """
    if not has_existing_data("records"):
        log.info("Install fresh database")
        execute_sql_schema(sql_schema)
        execute_sql_schema(create_metadata_table)

    else:
        log.debug("Database already exists!")


def migrate(sql_schemas_path, pdns_app_version_raw):
    """
        Compares the running application version with the database version.
        If the database version is older than the application version it will run an schema upgrade.
    """
    if pdns_app_version_raw is None or pdns_app_version_raw == "":
        log.error(
            "Missing value from PowerDNS. Should be something like '4.1.0'")
        log.info("Cannot continue... Killing!")
        sys.exit(1)

    else:
        pdns_app_version = version.parse(pdns_app_version_raw)
        log.debug(f"PowerDNS version: {pdns_app_version_raw}")

    pdns_db_version = get_pdns_db_version()  # Refresh version from DB

    if pdns_app_version.major == pdns_db_version.major and pdns_app_version.minor == pdns_db_version.minor:
        log.info("No DB upgrade needed... Continuing")

    elif pdns_app_version.major == pdns_db_version.major and pdns_app_version.minor > pdns_db_version.minor:
        log.info("Found new version. Atempting schema upgrade!")
        log.debug(f"Walking {sql_schemas_path}")

        for dir_path, subdir_list, file_list in os.walk(sql_schemas_path):
            filenames = sorted(file_list)
            log.debug(f"Sorted filenames: {filenames}")

            for filename in filenames:
                schema_old, schema_new = parse_sql_schema_filename(filename)
                pdns_db_version = get_pdns_db_version()  # Refresh DB version

                if schema_old.major == pdns_db_version.major and schema_old.minor == pdns_db_version.minor and pdns_app_version.major == schema_new.major and pdns_app_version.minor >= schema_new.minor:
                    full_path = os.path.join(dir_path, filename)
                    log.info(f"Found match: {filename}")
                    log.debug(f"Full Path: {full_path}")
                    execute_sql_schema(full_path)
                    bump_pdns_db_version(schema_new, schema_old)
                    log.info(f"Upgraded from {schema_old} to {schema_new}")

                else:
                    log.debug(f"Skipping: {filename}")
    elif pdns_app_version.major == pdns_db_version.major and pdns_app_version.minor > pdns_db_version.minor:
        log.error(
            f"The pdns_db version cannot be newer than the pdns_app version! Please update the app :)"
        )
        sys.exit(1)

    else:
        log.error(f"This should not be possible!")
        sys.exit(1)
