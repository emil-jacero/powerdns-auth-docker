#!/usr/bin/env python3

# TODO: Implement something that can handle variable input from environment

import os
import jinja2
from lib.logger import create_logger


# Create logger
log = create_logger(name='template')


def render_template(template, output_file, config):
    """
        Takes template, output file and dictionary of variables.
        Renders template with variables to the specified output file.
    """
    # Separate path from file
    path = os.path.dirname(template)
    name = os.path.basename(template)
    log.debug(f"Template path: {'Path_not_provided' if path is '' else path}")
    log.debug(f"Template name: {name}")

    # Remove file if exists
    if os.path.exists(output_file):
        log.info(f"Removing old file")
        os.remove(output_file)

    # Write rendered template into file
    log.info(f"Rendering template [{output_file}]")
    with open(output_file, 'w') as f:
        f.write(load_template(name, path).render(config))


def load_template(name, path=None):
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
