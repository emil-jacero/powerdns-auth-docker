#!/usr/bin/env python3

import os
import sys
import psycopg2
import time
import subprocess
import logging

from lib.logger import logger
from lib.config import Config
from lib.template import Template
from lib.migrations import PSQL, Migration, run_migrations


logger_name = f'{Config.logger_name}.entrypoint'
log = logging.getLogger(logger_name)


# Init Config and Migration
config = Config()
mig = Migration(config)
script_path = os.path.dirname(os.path.realpath(__file__))
sql_upgrade_scripts = os.path.join(script_path, 'sql_upgrade_scripts')
sql_schemas = os.path.join(script_path, 'sql_schemas')


def wait_for_db(user, password, host, port):
    try:
        conn_string = f"host={host} port={port} user={user} password={password} connect_timeout=1"
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
renderer = Template("pdns.conf.j2")
renderer.render_template("/etc/powerdns/pdns.conf", config.get_envs_for_template(config.get_extra_envs()))


# Wait for DB
while wait_for_db(user=config.pgsql_user,
                  password=config.pgsql_password,
                  host=config.pgsql_host,
                  port=config.pgsql_port) is False:
    log.info(f"Waiting for postgres at: {config.pgsql_host}:{config.pgsql_port}")
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
    log.info("Database already exists!")


# Run migrations
if config.pdns_run_mode == "MASTER":
    run_migrations(mig, sql_upgrade_scripts, config.get_pdns_version())
elif config.pdns_run_mode == "SLAVE":
    update_supermaster = os.path.join(sql_schemas, 'update_supermaster.sql')
    renderer = Template("update_supermaster.sql.j2")
    renderer.render_template(update_supermaster, config.get_envs_for_template(config.get_extra_envs()))
    mig.execute_sql_schema(update_supermaster)
    run_migrations(mig, sql_upgrade_scripts, config.get_pdns_version())
else:
    log.error(f"The environment variable 'ENV_PDNS_MODE' must be set to either MASTER or SLAVE")
    sys.exit(1)


# Launch PowerDNS
command1 = ["pdns_server", "--guardian=no", "--daemon=no", "--disable-syslog", "--write-pid=no"]
log.info("Starting PowerDNS")
process = subprocess.Popen(command1, shell=False)
process.wait()
log.info("PowerDNS stopped")

