#!/usr/bin/env python3

import os
import sys
import psycopg2
import time
import subprocess
from lib.config import config
from lib.logger import create_logger
from lib.template import render_template
from lib.migrations import PSQL, Migration, run_migrations


# Create logger
log = create_logger(name='entrypoint')


# Init Config and Migration
config = config()
mig = Migration(config)
script_path = os.path.dirname(os.path.realpath(__file__))
sql_upgrade_scripts = os.path.join(script_path, 'sql_upgrade_scripts')
sql_schemas = os.path.join(script_path, 'sql_schemas')


def wait_for_db():
    try:
        conn_string = f"user={config['PDNS_PGSQL_USER']} " \
                      f"host={config['PDNS_PGSQL_HOST']} " \
                      f"port={config['PDNS_PGSQL_PORT']} " \
                      f"password={config['PDNS_PGSQL_PASSWORD']} " \
                      f"connect_timeout=1"
        conn = psycopg2.connect(conn_string)
        conn.close()
        return True
    except:
        return False

def has_existing_data(table_name):
    """
        Query for table domains and records
        If they exist and has content return true
    """
    query = f"select exists(select * from information_schema.tables where table_name='{table_name}')"
    conn = PSQL(config)
    cursor = conn.cursor_create()
    cursor.execute(query)
    record = cursor.fetchone()[0]
    if record is True:
        return True
    else:
        return False


# Write configuration files
try:
    dev = os.environ['DEV']
except:
    dev = "false"
if dev == "true":
    render_template("pdns.conf.j2", "./pdns.conf_test", config)
else:
    render_template("pdns.conf.j2", "/etc/powerdns/pdns.conf", config)


# Wait for DB
while wait_for_db() is False:
    log.info(f"Waiting for postgres at: {config['PDNS_PGSQL_HOST']}:{config['PDNS_PGSQL_PORT']}")
    time.sleep(2)


# Install fresh database if empty
if has_existing_data("records") is False:
    # Install DB
    log.info("Install fresh database")
    sql_schema_path = os.path.join(sql_schemas, '4.1.0_schema.pgsql.sql')
    create_metadata_table = os.path.join(sql_schemas, 'create_metadata_table.sql')
    mig.execute_sql_schema(sql_schema_path)
    mig.execute_sql_schema(create_metadata_table)
else:
    log.info("Database already exists")


# Run migrations
if config['ENV_PDNS_MODE'] == "MASTER":
    run_migrations(mig, sql_upgrade_scripts)
elif config['ENV_PDNS_MODE'] == "SLAVE":
    update_supermaster = os.path.join(sql_schemas, 'update_supermaster.sql')
    render_template("update_supermaster.sql.j2", update_supermaster, config)
    mig.execute_sql_schema(update_supermaster)
    run_migrations(mig, sql_upgrade_scripts)


# Launch PowerDNS
command1 = ["pdns_server", "--guardian=no", "--daemon=no", "--disable-syslog", "--write-pid=no"]
log.info("Starting PowerDNS")
process = subprocess.Popen(command1, shell=False)
process.wait()
log.info("PowerDNS stopped")

