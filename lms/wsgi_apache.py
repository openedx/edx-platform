import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")
# This application object is used by the development server
# as well as any WSGI server configured to use this file.
from django.core.wsgi import WSGIHandler
_application = WSGIHandler()

def application(environ, start_response):
    #copy SERVICE_VARIANT from apache environ to os environ 
    os.environ.setdefault("SERVICE_VARIANT", environ.get("SERVICE_VARIANT", "lms"))
    return _application(environ, start_response)

from django.conf import settings
from xmodule.modulestore.django import modulestore

for store_name in settings.MODULESTORE:
    modulestore(store_name)
