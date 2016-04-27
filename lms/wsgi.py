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

import openedx.core.operations
openedx.core.operations.install_memory_dumper()

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
application = get_wsgi_application()  # pylint: disable=invalid-name
