# pylint: disable=missing-docstring
from __future__ import absolute_import

from django.conf import settings

if hasattr(settings, "COMMENTS_SERVICE_URL"):
    SERVICE_HOST = settings.COMMENTS_SERVICE_URL
else:
    SERVICE_HOST = 'http://localhost:4567'

PREFIX = SERVICE_HOST + '/api/v1'
