# Patch the xml libs before anything else.
from safe_lxml import defuse_xml_libs
defuse_xml_libs()

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
os.environ.setdefault("SERVICE_VARIANT", "lms")

import lms.startup as startup
startup.run()

# This application object is used by the development server
# as well as any WSGI server configured to use this file.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
