#!/usr/bin/env python3

import os
import jinja2

class Template:
    def __init__(self, template, env_search_term="ENV"):
        # Separate path from file
        self.path = os.path.dirname(template)
        self.name = os.path.basename(template)
        self.env_search_term = env_search_term
        self.variables = self.get_variables()

    def get_variables(self):
        result = {}
        for k,v in os.environ.items():
            if self.env_search_term in k:
                obj = {k : v}
                result.update(obj)
        return result

    def render_template(self, output_file):
        """
            Takes template, output file and dictionary of variables.
            Renders template with variables to the specified output file.
        """
        # Remove file if exists
        if os.path.exists(output_file):
            os.remove(output_file)

        # Write rendered template into file
        with open(output_file, 'w') as f:
            f.write(self._load_template(self.name, self.path).render(self.variables))

    def _load_template(self, name, path=None):
        """
            Takes template name and a path to the template directory
        """
        # Guessing templates directory
        if path is None or path == "":
            path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(path))
        return env.get_template(name)


test = Template(template="derp.conf.j2")
test.render_template(output_file="derp.conf")
test.get_variables()
