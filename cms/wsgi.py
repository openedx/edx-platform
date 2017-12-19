# Patch the xml libs before anything else. Because this makes imports out-of-order, disable pylint errors.
# pylint: disable=wrong-import-order, wrong-import-position
from safe_lxml import defuse_xml_libs
defuse_xml_libs()

import os

# Disable PyContract contract checking when running as a webserver
import contracts
# This application object is used by the development server
# as well as any WSGI server configured to use this file.
from django.core.wsgi import get_wsgi_application

import cms.startup as startup

contracts.disable_all()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cms.envs.aws")

startup.run()

application = get_wsgi_application()
