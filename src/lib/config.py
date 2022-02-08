import os
import sys
from packaging import version
from logging import Formatter, DEBUG, INFO, WARNING, ERROR, StreamHandler, FileHandler


def parse_sql_schema_filename(filename):
    old_version = version.parse(filename.split('_')[0])
    new_verion = version.parse(filename.split('_')[2])
    return old_version, new_verion


def get_from_environment(env_search_term="ENV"):
    enviroment = {}
    autosecondary = {}
    for k, v in os.environ.items():

        if f"{env_search_term}_" in k:
            k = k.replace(f"{env_search_term}_", "").replace("_", "-").lower()
            obj = {k: v}
            enviroment.update(obj)

        elif ("SUPERSLAVE" in k) or ("AUTOSECONDARY" in k):
            obj = {k: v}
            autosecondary.update(obj)

    return enviroment, autosecondary


def get_from_file(file):
    conf_list = []
    pdns_config = {}
    try:
        f = open(file, "r")
        conf_list = list(map(lambda s: s.strip(), f))
        conf_list = [x for x in conf_list if x]
        for line in conf_list:
            split_line = line.split("=")
            obj = {split_line[0]: split_line[1]}
            pdns_config.update(obj)
    except Exception as error:
        print(error)
    return pdns_config


def merge_dicts(defaults_dict, dict_list):
    for dict in dict_list:
        defaults_dict.update(dict)
    if "gpgsql-dbname" in defaults_dict:  # TODO: Extend with more databases
        defaults_dict.pop('gsqlite3-database', None)
        defaults_dict.pop('gsqlite3-pragma-synchronous', None)
    return defaults_dict


class Config:
    powerdns_app_version = os.environ['POWERDNS_VERSION']
    exec_mode = os.environ['EXEC_MODE']  # DOCKER or K8S

    # Default pdns config as dict
    defaults = {
        "setuid": 101,
        "setgid": 101,
        "primary": "yes",
        "secondary": "no",
        "launch": "gsqlite3",
        "gsqlite3-database": "/var/lib/powerdns/auth.db",
        "gsqlite3-pragma-synchronous": 0,
        "local-address": "0.0.0.0",
        "local-port": "53",
    }

    # Read config from file (/pdns.conf) and parse to dict
    file_conf = get_from_file("/pdns.conf")

    # Read config from Environment variables (ENV_) and parse to dict
    env_conf, autosecondary = get_from_environment("ENV")

    # Merge all configs in this specific order. Higher number higher priority
    # 1. Defaults
    # 2. File
    # 3. Environment variables
    pdns_conf = merge_dicts(defaults, [file_conf, env_conf])

    # Set database config
    ## PostgreSQL
    gpgsql_dbname = pdns_conf.get('gpgsql-dbname')
    gpgsql_user = pdns_conf.get('gpgsql-user')
    gpgsql_password = pdns_conf.get('gpgsql-password')
    gpgsql_host = pdns_conf.get('gpgsql-host')
    gpgsql_port = pdns_conf.get('gpgsql-port')
    ## SQLite
    gsqlite3_path = pdns_conf.get('gsqlite3-database')

    # PATHS
    base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sql_schema_path = os.path.join(base_dir, 'sql_schemas')
    sql_update_schemas_path = os.path.join(base_dir, 'sql_update_schemas')
    template_path = os.path.join(base_dir, 'templates')

    # LOGGING
    logger_name = 'pdns_auth'
    formatter = Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    log_levels = {
        'DEBUG': DEBUG,
        'INFO': INFO,
        'WARNING': WARNING,
        'ERROR': ERROR
    }
    env_log_level = os.getenv('LOG_LEVEL')
    if env_log_level in log_levels.keys():
        log_level = log_levels[env_log_level]
    else:
        log_level = INFO

    logg_handlers = []

    try:
        handler: StreamHandler = StreamHandler()
        logg_handlers.append(handler)
    except Exception as e:
        print('Unexpected error: (StreamHandler)', sys.exc_info()[0])
