#!/usr/bin/env python3

# TODO: Implement something that can handle variable input from environment

import os
import jinja2
import logging

from lib.config import Config


logger_name = f'{Config.logger_name}.template'
log = logging.getLogger(logger_name)

class Template:
    def __init__(self, template):
        self._logger = logging.getLogger(f'{logger_name}.{self.__class__.__name__}')
        # Separate path from file
        self.path = os.path.dirname(template)
        self.name = os.path.basename(template)
        log.debug(f"Template path: {'Path_not_provided' if self.path is '' else self.path}")
        log.debug(f"Template name: {self.name}")


    def render_template(self, output_file, config):
        """
            Takes template, output file and dictionary of variables.
            Renders template with variables to the specified output file.
        """
        # Remove file if exists
        if os.path.exists(output_file):
            log.info(f"Removing old file [{output_file}]")
            os.remove(output_file)

        # Write rendered template into file
        log.info(f"Rendering template [{output_file}]")
        with open(output_file, 'w') as f:
            f.write(self.load_template(self.name, self.path).render(config))

    def load_template(self, name, path=None):
        """
            Takes template name and a path to the template directory
        """
        # Guessing templates directory
        if path is None or path == "":
            path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')
            log.info(f"Missing path to templates. Using default...")
            log.info(f"Default path: {path}")
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(path))
        return env.get_template(name)
