from importlib import import_module
from django.conf import settings

def autostartup():
    """
    Execute app.startup:run() for all installed django apps
    """
    for app in settings.INSTALLED_APPS:
        try:
            mod = import_module(app + '.startup')
            if hasattr(mod, 'run'):
                mod.run()
        except ImportError:
            continue
