# Disable PyContract contract checking when running as a webserver
import contracts
contracts.disable_all()

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cms.envs.aws")

import cms.startup as startup
startup.run()

# This application object is used by the development server
# as well as any WSGI server configured to use this file.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

