import os
import sys
from packaging import version
from logging import Formatter, DEBUG, INFO, WARNING, ERROR, StreamHandler, FileHandler


def parse_sql_schema_filename(filename):
    old_version = version.parse(filename.split('_')[0])
    new_verion = version.parse(filename.split('_')[2])
    return old_version, new_verion


def get_environment(env_search_term="ENV"):
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


class Config:
    enviroment, autosecondary = get_environment("ENV")

    #GLOBAL
    powerdns_app_version = os.environ['POWERDNS_VERSION']
    if int(powerdns_app_version) >= 45:
        if enviroment.get('primary') == 'yes':
            pdns_mode = "primary"
        else:
            pdns_mode = "secondary"
    else:
        if enviroment.get('master') == 'yes':
            pdns_mode = "primary"
        else:
            pdns_mode = "secondary"

    # PATHS
    base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sql_schema_path = os.path.join(base_dir, 'sql_schemas')
    sql_update_schemas_path = os.path.join(base_dir, 'sql_update_schemas')
    template_path = os.path.join(base_dir, 'templates')

    # SQLite
    gsqlite3_db_path = '/var/lib/powerdns/auth.db'

    # PostgreSQL
    gpgsql_dbname = enviroment.get('gpgsql-dbname')
    gpgsql_user = enviroment.get('gpgsql-user')
    gpgsql_password = enviroment.get('gpgsql-password')
    gpgsql_host = enviroment.get('gpgsql-host')
    gpgsql_port = enviroment.get('gpgsql-port')

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