#!/usr/bin/env python3

import os
import sys
import subprocess
import json

from lib.logger import logger as log
from lib.config import Config
from lib.template import Template

# Set working directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# Init
renderer = Template()

# Log the configuration for debuging. OBS! The password is visible. Do not run in a production environment
log.debug(json.dumps(Config.pdns_conf, indent=2))
log.debug(json.dumps(Config.autosecondary, indent=2))


def gen_pdns_version():
    result = None
    name = str(Config.powerdns_app_version)
    result = f'{name[0]}.{name[1]}.0'
    return result


def gpgsql():
    from lib.migrations.gpgsql import install, migrate, execute_sql_schema, wait_for_db

    log.debug("Discovered PostgreSQL")
    sql_update_schemas_path = os.path.join(Config.sql_update_schemas_path,
                                           'gpgsql')
    wait_for_db()
    install()  # Install fresh db only if it does not exists.
    if Config.pdns_conf.get('primary') == 'yes' or Config.pdns_conf.get(
            'master') == 'yes':
        migrate(sql_update_schemas_path, gen_pdns_version())

    elif Config.pdns_conf.get('secondary') == 'yes' or Config.pdns_conf.get(
            'slave') == 'yes':
        autosecondary_sql = os.path.join(Config.sql_schema_path,
                                         "update_supermaster.pgsql.sql")
        log.debug(f"Autosecondary SQL path: {autosecondary_sql}")
        renderer.render_template(template=os.path.join(
            Config.template_path, "update_supermaster.pgsql.sql.j2"),
                                 output_file=autosecondary_sql)
        execute_sql_schema(autosecondary_sql)
        migrate(sql_update_schemas_path, gen_pdns_version())


def gsqlite3():
    from lib.migrations.gsqlite3 import install, migrate, execute_sql_schema

    log.debug("Discovered SQLite")
    sql_update_schemas_path = os.path.join(Config.sql_update_schemas_path,
                                           'gsqlite3')
    install()  # Install fresh db only if it does not exists.
    if Config.pdns_conf.get('primary') == 'yes' or Config.pdns_conf.get(
            'master') == 'yes':
        migrate(sql_update_schemas_path, gen_pdns_version())

    elif Config.pdns_conf.get('secondary') == 'yes' or Config.pdns_conf.get(
            'slave') == 'yes':
        autosecondary_sql = os.path.join(Config.sql_schema_path,
                                         "update_supermaster.sqlite3.sql")
        log.debug(f"Autosecondary SQL path: {autosecondary_sql}")
        renderer.render_template(template=os.path.join(
            Config.template_path, "update_supermaster.sqlite3.sql.j2"),
                                 output_file=autosecondary_sql)
        execute_sql_schema(autosecondary_sql)
        migrate(sql_update_schemas_path, gen_pdns_version())


if "gpgsql" in Config.pdns_conf['launch']:
    gpgsql()
elif "gsqlite3" in Config.pdns_conf['launch']:
    gsqlite3()
else:
    log.error("No backend discovered")
    sys.exit(1)

# Write PowerDNS configuration
template = os.path.join(Config.template_path, "pdns.conf.j2")
renderer.render_template(template=template,
                         output_file="/etc/powerdns/pdns.conf")

# Launch PowerDNS
command1 = [
    "pdns_server", "--guardian=no", "--daemon=no", "--disable-syslog",
    "--write-pid=no"
]
log.info("Starting PowerDNS")
process = subprocess.Popen(command1, shell=False)
process.wait()
log.info("PowerDNS stopped")
