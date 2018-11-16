from .aws import *
from django.conf import settings

EDX_PLATFORM_STATIC_ROOT_BASE = settings.STATIC_ROOT_BASE

STATIC_ROOT_BASE=os.environ.get('STATIC_COLLECTOR_ROOT', '/edx/var/edxapp/static_collector')
STATIC_ROOT = path(STATIC_ROOT_BASE)
