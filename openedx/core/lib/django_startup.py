"""
Extend startup behavior shared between LMS and CMS
"""

from importlib import import_module
from django.conf import settings


def add_mimetypes():
    """
    Add extra mimetype mappings
    """
    import mimetypes

    mimetypes.add_type('application/vnd.ms-fontobject', '.eot')
    mimetypes.add_type('application/x-font-opentype', '.otf')
    mimetypes.add_type('application/x-font-ttf', '.ttf')
    mimetypes.add_type('application/font-woff', '.woff')


def autostartup():
    """
    Execute app.startup:run() for all installed django apps
    """
    for app in settings.INSTALLED_APPS:
        # See if there's a startup module in each app.
        try:
            mod = import_module(app + '.startup')
        except ImportError:
            continue

        # If the module has a run method, run it.
        if hasattr(mod, 'run'):
            mod.run()
