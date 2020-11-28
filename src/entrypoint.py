#!/usr/bin/env python3

import os
import sys
import psycopg2
import time
import subprocess
import logging

from lib.logger import logger as log
from lib.config import Config
from lib.template import Template
from lib.migrations import PSQL, Migration, migrate

# Set working directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# Init
mig = Migration()
renderer = Template(env_search_term="ENV")

# Write configuration files
pdns_conf_template = os.path.join(Config.template_path, "pdns.conf.j2")
renderer.render_template(template=pdns_conf_template, output_file="/etc/powerdns/pdns.conf")

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
    conn = PSQL(pdns_pgsql_host=Config.pdns_pgsql_host,
                 pdns_pgsql_port=Config.pdns_pgsql_port,
                 pdns_pgsql_dbname=Config.pdns_pgsql_dbname,
                 pdns_pgsql_user=Config.pdns_pgsql_user,
                 pdns_pgsql_password=Config.pdns_pgsql_password)
    cursor = conn.cursor_create()
    cursor.execute(query)
    record = cursor.fetchone()[0]
    if record is True:
        return True
    else:
        return False

def gen_pdns_version():
        result = None
        name = str(Config.powerdns_repo_version)
        result = f'{name[0]}.{name[1]}.0'
        return result

# Wait for database to come up
while wait_for_db(host=Config.pdns_pgsql_host,
                port=Config.pdns_pgsql_port,
                user=Config.pdns_pgsql_user,
                password=Config.pdns_pgsql_password) is False:
    log.info(f"Waiting for postgres at: {Config.pdns_pgsql_host}:{Config.pdns_pgsql_port}")
    time.sleep(2)

# Install fresh database if empty
if has_existing_data("records") is False:
    # Install DB
    log.info("Install fresh database")
    sql_schema = os.path.join(Config.sql_schema_path, '4.1.0_schema.pgsql.sql')
    create_metadata_table = os.path.join(Config.sql_schema_path, 'create_metadata_table.sql')
    mig.execute_sql_schema(sql_schema)
    mig.execute_sql_schema(create_metadata_table)
else:
    log.info("Database already exists!")

# Run migrations
if Config.pdns_run_mode == "MASTER":

    migrate(mig, Config.sql_schema_update_path, gen_pdns_version())
elif Config.pdns_run_mode == "SLAVE":
    supermaster_sql = os.path.join(Config.sql_schema_path, 'update_supermaster.sql')
    renderer.render_template(template=os.path.join(Config.template_path, "update_supermaster.sql.j2"), output_file=supermaster_sql)
    mig.execute_sql_schema(supermaster_sql)
    migrate(mig, Config.sql_schema_update_path, gen_pdns_version())
else:
    log.error(f"The environment variable 'ENV_PDNS_MODE' must be set to either MASTER or SLAVE")
    sys.exit(1)


# Launch PowerDNS
command1 = ["pdns_server", "--guardian=no", "--daemon=no", "--disable-syslog", "--write-pid=no"]
log.info("Starting PowerDNS")
process = subprocess.Popen(command1, shell=False)
process.wait()
log.info("PowerDNS stopped")
