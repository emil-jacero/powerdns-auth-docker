import os
import json
from lib.logger import create_logger


# Create logger
log = create_logger(name='config')


def config():
    env_dict = {}
    try:
        env_dict['PDNS_PGSQL_DBNAME'] = os.environ['PDNS_PGSQL_DBNAME']
        env_dict['PDNS_PGSQL_USER'] = os.environ['PDNS_PGSQL_USER']
        env_dict['PDNS_PGSQL_PASSWORD'] = os.environ['PDNS_PGSQL_PASSWORD']
        env_dict['PDNS_PGSQL_HOST'] = os.environ['PDNS_PGSQL_HOST']
        env_dict['PDNS_PGSQL_PORT'] = os.environ['PDNS_PGSQL_PORT']
    except KeyError as e:
        log.error(f"Missing environment variable [{e.args[0]}]")
        log.error(e)

    for k, v in os.environ.items():
        if "ENV_" in k:
            env_dict[k] = v

    log.info("Loaded config from environment!")
    log.debug(json.dumps(env_dict))

    return env_dict
