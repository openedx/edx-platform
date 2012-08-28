import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")

# This application object is used by the development server
# as well as any WSGI server configured to use this file.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from django.conf import settings
from xmodule.modulestore.django import modulestore

for store_name in settings.MODULESTORE:
    modulestore(store_name)
