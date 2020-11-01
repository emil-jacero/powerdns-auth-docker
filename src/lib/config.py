import os
import json
from logging import Formatter, INFO, WARNING, ERROR, DEBUG, getLogger



class Config:
    # LOGGING
    logger_name = 'pdns_auth_docker'
    # Create formatter
    formatter: Formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    

    def __init__(self):
        self._logger = getLogger(f'{self.logger_name}.{self.__class__.__name__}')
        self.powerdns_repo_version = os.environ['POWERDNS_VERSION']

        # Logging level
        #if not os.environ['DEBUG']:
        #    self.logging_level = DEBUG
        #else:
        self.logging_level = DEBUG

        # Read the desired run mode
        self.pdns_run_mode = os.environ['ENV_PDNS_MODE']

        self.pgsql_dbname = os.environ['PDNS_PGSQL_DBNAME']
        self.pgsql_user = os.environ['PDNS_PGSQL_USER']
        self.pgsql_password = os.environ['PDNS_PGSQL_PASSWORD']
        self.pgsql_host = os.environ['PDNS_PGSQL_HOST']
        self.pgsql_port = os.environ['PDNS_PGSQL_PORT']

    def get_extra_envs(self):
        extra_envs = {'PDNS_PGSQL_DBNAME': f'{self.pgsql_dbname}',
                      'PDNS_PGSQL_USER': f'{self.pgsql_user}',
                      'PDNS_PGSQL_PASSWORD': f'{self.pgsql_password}',
                      'PDNS_PGSQL_HOST': f'{self.pgsql_host}',
                      'PDNS_PGSQL_PORT': f'{self.pgsql_port}'}
        return extra_envs

    def get_pdns_version(self):
        return self.convert_to_version_name(self.powerdns_repo_version)

    @staticmethod
    def get_envs_for_template(extra_envs: dict = {}):
        env_dict = {}
        for k, v in os.environ.items():
            if "ENV_" in k:
                env_dict[k] = v
        env_dict.update(extra_envs)
        return env_dict

    @staticmethod
    def convert_to_version_name(name):
        result = None
        name = str(name)
        result = f'{name[0]}.{name[1]}.0'
        return result

