import os
import jinja2
import logging

from lib.config import Config


class Template:
    def __init__(self):
        self.log_name = f'{Config.logger_name}.{self.__class__.__name__}'
        self.log = logging.getLogger(self.log_name)
        self.path = None
        self.name = None
        self.enviroment = Config.enviroment
        self.autosecondary = Config.autosecondary

    def render_template(self, template, output_file):
        """
            Takes template, output file and dictionary of variables.
            Renders template with variables to the specified output file.
        """
        self.path = os.path.dirname(template)
        self.name = os.path.basename(template)
        self.log.debug(
            f"Template path: {'Path_not_provided' if self.path == '' else self.path}"
        )
        self.log.debug(f"Template name: {self.name}")
        # Remove file if exists

        if os.path.exists(output_file):
            self.log.info(f"Removing old file [{output_file}]")
            os.remove(output_file)

        # Write rendered template into file
        self.log.info(f"Rendering template {template} to {output_file}")
        data = self.enviroment
        autosecondary = self.autosecondary

        with open(output_file, 'w') as f:
            f.write(
                self._load_template(self.name, self.path).render(
                    data=data, autosecondary=autosecondary))

    def _load_template(self, name, path=None):
        """
            Takes template name and a path to the template directory
        """
        # Guessing templates directory
        if path is None or path == "":
            path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                'templates')
            self.log.info(f"Missing path to templates. Using default...")
            self.log.debug(f"Template path: {path}")

        else:
            self.log.debug(f"Template path: {path}")
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(path))

        return env.get_template(name)
