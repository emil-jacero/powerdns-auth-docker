import os
import json
from logging import Formatter, INFO, WARNING, ERROR, DEBUG, getLogger

import os
import sys
from logging import Formatter, DEBUG, INFO, WARNING, ERROR, StreamHandler, FileHandler


class Config:
    #GLOBAL
    powerdns_repo_version = os.environ['POWERDNS_VERSION']
    pdns_run_mode = os.getenv('ENV_PDNS_MODE')

    # ROOT DIR
    base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    # PATH
    sql_schema_update_path = os.path.join(base_dir, 'src/sql_schema_updates')
    sql_schema_path = os.path.join(base_dir, 'src/sql_schemas')
    template_path = os.path.join(base_dir, 'src/templates')

    # LOGGING
    logger_name = 'pdns_auth_docker'

    log_levels = {'DEBUG': DEBUG, 'INFO': INFO, 'WARNING': WARNING, 'ERROR': ERROR}
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

    # POSTGRESQL
    pdns_pgsql_dbname = os.getenv('ENV_PDNS_PGSQL_DBNAME')
    pdns_pgsql_user = os.getenv('ENV_PDNS_PGSQL_USER')
    pdns_pgsql_password = os.getenv('ENV_PDNS_PGSQL_PASSWORD')
    pdns_pgsql_host = os.getenv('ENV_PDNS_PGSQL_HOST')
    pdns_pgsql_port = os.getenv('ENV_PDNS_PGSQL_PORT')
