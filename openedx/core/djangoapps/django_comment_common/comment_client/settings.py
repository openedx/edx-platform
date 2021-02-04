from django.conf import settings  # lint-amnesty, pylint: disable=cyclic-import, missing-module-docstring

if hasattr(settings, "COMMENTS_SERVICE_URL"):
    SERVICE_HOST = settings.COMMENTS_SERVICE_URL
else:
    SERVICE_HOST = 'http://localhost:4567'

PREFIX = SERVICE_HOST + '/api/v1'
