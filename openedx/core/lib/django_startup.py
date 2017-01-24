"""
Automatic execution of startup modules in Django apps.
"""

from importlib import import_module
from django.conf import settings


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
