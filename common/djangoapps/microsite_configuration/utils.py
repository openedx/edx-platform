import json
import os

from django.conf import settings


def get_initial_sass_variables():
    """
    This method loads the SASS variables file from the currently active theme. It is used as a default value
    for the sass_variables field on new Microsite objects.
    """
    sass_var_file = os.path.join(settings.ENV_ROOT, "themes",
                                 settings.THEME_NAME, 'src', 'base', '_branding-basics.scss')
    with open(sass_var_file, 'r') as f:
        return f.read()


def sass_to_dict(sass_input):
    sass_vars = {}
    lines = (line for line in sass_input.splitlines() if line and not line.startswith('//'))
    for line in lines:
        key, val = line.split(':')
        val = val.split('//')[0]
        val = val.strip().replace(";", "")
        sass_vars[key] = val
    return sass_vars


def sass_to_json_string(sass_input):
    sass_dict = sass_to_dict(sass_input)
    return json.dumps(sass_dict, sort_keys=True, indent=2)


def json_to_sass(json_input):
    sass_vars = json.loads(json_input)
    sass_text = ', '.join("{}={};".format(key, val) for (key, val) in sass_vars.iteritems())
    return sass_text
