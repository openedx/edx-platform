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

def sass_to_json(sass_input):
    pass
