import os
import sys
from pathlib import Path
import logging
from packaging import version
import sqlite3

from lib.config import Config, parse_sql_schema_filename
from lib.logger import logger as log
'''
    SQL migration DLL's are copied from upstream powerdns
    https://github.com/PowerDNS/pdns/tree/master/modules/gsqlite3backend
'''

log_name = f"{Config.logger_name}.gsqlite3"
log = logging.getLogger(log_name)
sql_schema = os.path.join(Config.sql_schema_path, "4.1.0_schema.sqlite3.sql")
create_metadata_table = os.path.join(Config.sql_schema_path,
                                     "create_metadata_table.sqlite3.sql")


class DB:
    def __init__(self):
        self.log_name = f"{log_name}.{self.__class__.__name__}"
        self.log = logging.getLogger(self.log_name)
        self.db = Config.gsqlite3_path

        self.conn_obj = None
        self.cursor_obj = None

    def connection(self):
        try:
            conn = sqlite3.connect(self.db)
            self.log.debug(f"Connected to database [{self.db}]")
            return conn

        except (Exception, sqlite3.Error) as error:
            self.log.error(f"Unable to connect to the database [{self.db}]")
            self.log.error(error)
            sys.exit(1)

    def create_cursor(self):
        self.conn_obj = self.connection()
        self.cursor_obj = self.conn_obj.cursor()
        return self.cursor_obj

    def close_all(self):
        try:
            self.conn_obj.close()
            self.log.debug("Connection Closed")
        except (Exception, sqlite3.Error) as error:
            self.log.error(error)

    def commit(self):
        #self.log.debug(f"Committing SQL query [{self.cursor_obj}]")
        self.conn_obj.commit()

    def rollback(self):
        #self.log.debug(f"Rolling back SQL query [{self.cursor_obj}]")
        self.conn_obj.rollback()


def get_pdns_db_version():
    """
        Grab the PowerDNS version stored in pdns_meta and exits the program if missing
    """
    record = execute_single_query("SELECT db_version FROM pdns_meta")
    if record is None or record == "":
        log.error(
            "Missing value in column db_version in table pdns_meta. Should be something like '4.1.0'"
        )
    else:
        pdns_db_version = version.parse(record)
        log.debug(f"Database version: {record}")
        return pdns_db_version


def execute_single_query(query):
    """
        Execute a single query.
    """
    conn = DB()
    try:
        log.debug(f"Query: {query}")
        cursor = conn.create_cursor()
        cursor.execute(query)
        conn.commit()
        record = cursor.fetchone()[0]
        return record

    except (Exception, sqlite3.Error) as error:
        conn.rollback()
        log.error(error)
        sys.exit(1)

    finally:
        if conn is not None:
            conn.close_all()


def execute_sql_schema(file_path):
    """
        Execute a single file.
    """
    conn = DB()
    try:
        cursor = conn.create_cursor()
        cursor.executescript(open(file_path, "r").read())
        conn.commit()
        log.info(f"Committed schema to database: {file_path}")

    except (Exception, sqlite3.Error) as error:
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
        query = f"UPDATE pdns_meta SET db_version='{new_version}', db_version_previous='{old_version}' WHERE db_version='{old_version}'"
        log.debug(f"Bumping DB version: [{old_version} -> {new_version}]")
        cursor.execute(query)
        conn.commit()

    except (Exception, sqlite3.Error) as error:
        conn.rollback()
        log.error(
            f"Was unable to bump the version number to the latest! [{old_version} -> {new_version}]"
        )
        log.debug(error)
        sys.exit(1)

    finally:
        if conn is not None:
            conn.close_all()


def has_existing_table(table_name):
    """
        Return True if the given table name exists.
    """
    conn = DB().connection()
    query = f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table_name}';"
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        if not cursor.fetchone()[0]:
            result = False
        else:
            result = True

    except (Exception) as error:
        conn.rollback()
        conn.close()
        log.error(error)
        sys.exit(1)

    conn.commit()
    conn.close()
    return result


def install():
    """
        Creates new DB if it does not exist. Also populates it with an empty schema if it does not exist
    """
    Path(Config.gsqlite3_path).touch()
    conn = None
    try:
        conn = sqlite3.connect(Config.gsqlite3_path)
        log.info(f"SQLite version: {sqlite3.version}")

    except sqlite3.Error as e:
        log.error(e)
        sys.exit(1)

    finally:
        if conn:
            conn.close()

    if not has_existing_table("records"):
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
