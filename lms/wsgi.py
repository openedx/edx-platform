"""
WSGI config for LMS.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments.
It exposes a module-level variable named ``application``. Django's
``runserver`` and ``runfcgi`` commands discover this application via the
``WSGI_APPLICATION`` setting.
"""

# Patch the xml libs
from safe_lxml import defuse_xml_libs
defuse_xml_libs()

# Disable PyContract contract checking when running as a webserver
import contracts
contracts.disable_all()

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.envs.aws")

import lms.startup as startup
startup.run()

from xmodule.modulestore.django import modulestore

# Trigger a forced initialization of our modulestores since this can take a
# while to complete and we want this done before HTTP requests are accepted.
modulestore()


# This application object is used by the development server
# as well as any WSGI server configured to use this file.
from django.core.wsgi import get_wsgi_application
_application = get_wsgi_application()


import logging
log = logging.getLogger(__name__)


class WsgiApp:
    def __init__(self, application):
        self.application = application
    def __call__(self, environ, start_response):
        path_info = environ.get('PATH_INFO')
        log.error("WsgiApp path_info={}".format(path_info))
        raise Exception("WsgiApp path_info={}".format(path_info))
        if path_info.rstrip('/') == '/foo':
            environ['newrelic.app_name'] = 'foo'
        elif path_info.rstrip('/') == '/bar':
            environ['newrelic.app_name'] = 'bar'
        return self.application(environ, start_response)

application = WsgiApp(_application)
