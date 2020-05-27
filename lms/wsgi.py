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
import logging
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from edx_django_utils.monitoring import set_custom_metric

from lms.lib.monitoring import get_configured_newrelic_app_name_suffix_handler, newrelic_single_app_name_suffix_handler

log = logging.getLogger(__name__)
_application = get_wsgi_application()
_newrelic_app_name_suffix_handler = get_configured_newrelic_app_name_suffix_handler()

class WsgiApp:
    """
    Custom WsgiApp enables overriding of the NewRelic app name as needed.
    """
    def __init__(self, application):
        self.application = application

    def _set_new_relic_app_name(self):
        if not _newrelic_app_name_suffix_handler:
            return

        try:
            path_info = environ.get('PATH_INFO')

            settings.
            log.error("WsgiApp path_info={}".format(path_info))
            if path_info.rstrip('/') == '/login':
                environ['newrelic.app_name'] = 'sandbox-robrap-edxapp-lms-login'
                log.error('Trying to change newrelic app name')
            elif path_info.rstrip('/') == '/bar':
                environ['newrelic.app_name'] = 'bar'

    def __call__(self, environ, start_response):
        if _newrelic_app_name_suffix_handler:
            try:
                path_info = environ.get('PATH_INFO')

                settings.
                log.error("WsgiApp path_info={}".format(path_info))
                if path_info.rstrip('/') == '/login':
                    environ['newrelic.app_name'] = 'sandbox-robrap-edxapp-lms-login'
                    log.error('Trying to change newrelic app name')
                elif path_info.rstrip('/') == '/bar':
                    environ['newrelic.app_name'] = 'bar'
            except Exception as e:
                try:
                    set_custom_metric('wsgi_mapping_error', e)
                except:
                    pass

        return self.application(environ, start_response)


application = WsgiApp(_application)
