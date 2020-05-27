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
import time
from django.core.wsgi import get_wsgi_application
from edx_django_utils.monitoring import set_custom_metric

from lms.lib.monitoring import get_configured_newrelic_app_name_suffix_handler

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
        """
        Sets the NewRelic app name based on the path, when path is mapped to a suffix.
        """
        if not _newrelic_app_name_suffix_handler:
            return

        try:
            request_path = environ.get('PATH_INFO')
            before_time = time.perf_counter()
            suffix = _newrelic_app_name_suffix_handler(request_path)
            if suffix:
                new_app_name = "{}-{}".format(environ['newrelic.app_name'], suffix)
                environ['newrelic.app_name'] = new_app_name
                # We may remove this metric later, but for now, it can be used to confirm that
                # the updated_app_name matches the app name, and that these set_custom_metric
                # calls are making it to the appropriate transaction.
                set_custom_metric('updated_app_name', new_app_name)
            after_time = time.perf_counter()
            # Tracking the time can be used to enable alerting if this ever gets too large.
            set_custom_metric('suffix_mapping_time', after_time - before_time)
        except Exception as e:
            set_custom_metric('suffix_mapping_error', e)

    def __call__(self, environ, start_response):
        try:
            self._set_new_relic_app_name()
        except Exception:
            log.exception("Unexpected error setting the NewRelic app name.")
        return self.application(environ, start_response)


application = WsgiApp(_application)
