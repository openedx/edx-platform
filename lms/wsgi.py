# Disable PyContract contract checking when running as a webserver
import contracts
contracts.disable_all()

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")

import lms.startup as startup
startup.run()

from django.conf import settings
from xmodule.modulestore.django import modulestore

# Trigger a forced initialization of our modulestores since this can take a
# while to complete and we want this done before HTTP requests are accepted.
modulestore()


# This application object is used by the development server
# as well as any WSGI server configured to use this file.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

