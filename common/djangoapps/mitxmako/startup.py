"""
Initialize the mako template lookup
"""

import tempdir
from django.conf import settings
from mako.lookup import TemplateLookup

import mitxmako


def run():
    """Setup mako variables and lookup object"""
    # Set all mako variables based on django settings
    template_locations = settings.MAKO_TEMPLATES
    module_directory = getattr(settings, 'MAKO_MODULE_DIR', None)

    if module_directory is None:
        module_directory = tempdir.mkdtemp_clean()

    lookup = {}

    for location in template_locations:
        lookup[location] = TemplateLookup(
            directories=template_locations[location],
            module_directory=module_directory,
            output_encoding='utf-8',
            input_encoding='utf-8',
            default_filters=['decode.utf8'],
            encoding_errors='replace',
        )

    mitxmako.lookup = lookup
