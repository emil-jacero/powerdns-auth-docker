#!/usr/bin/env python3

import os
import sys
import subprocess
import json
import ipaddress
import socket

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


def get_ipv4_by_hostname(hostname):
    return list(i[4][0] for i in socket.getaddrinfo(hostname, 0)
                if i[0] is socket.AddressFamily.AF_INET
                and i[1] is socket.SocketKind.SOCK_RAW)


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
        try:
            ip_from_env = ipaddress.ip_address(
                Config.autosecondary.get('AUTOSECONDARY_IP'))
            log.debug("AUTOSECONDARY_IP is a correct IP")
        except ValueError:
            log.debug("AUTOSECONDARY_IP is NOT a correct IP")
            try:
                resolved_ip = get_ipv4_by_hostname(
                    Config.autosecondary.get('AUTOSECONDARY_IP'))
                Config.autosecondary.update(
                    {'AUTOSECONDARY_IP': f'{resolved_ip}'})
            except:
                log.error(
                    f"Unable to resolve {Config.autosecondary.get('AUTOSECONDARY_IP')}"
                )
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
        try:
            ip_from_env = ipaddress.ip_address(
                Config.autosecondary.get('AUTOSECONDARY_IP'))
            log.debug("AUTOSECONDARY_IP is a correct IP")
        except ValueError:
            log.debug("AUTOSECONDARY_IP is NOT a correct IP")
            try:
                resolved_ip = get_ipv4_by_hostname(
                    Config.autosecondary.get('AUTOSECONDARY_IP'))
                Config.autosecondary.update(
                    {'AUTOSECONDARY_IP': f'{resolved_ip}'})
            except:
                log.error(
                    f"Unable to resolve {Config.autosecondary.get('AUTOSECONDARY_IP')}"
                )
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
