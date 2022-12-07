"""
Settings for Bok Choy tests that are used when running Studio in Docker-based devstack.
"""

# noinspection PyUnresolvedReferences
from .bok_choy import *  # pylint: disable=wildcard-import

CMS_BASE = '{}:{}'.format(os.environ['BOK_CHOY_HOSTNAME'], os.environ.get('BOK_CHOY_CMS_PORT', 8031))
LMS_BASE = '{}:{}'.format(os.environ['BOK_CHOY_HOSTNAME'], os.environ.get('BOK_CHOY_LMS_PORT', 8003))
LMS_ROOT_URL = f'http://{LMS_BASE}'
LOGIN_REDIRECT_WHITELIST = [CMS_BASE]
SITE_NAME = LMS_BASE

COMMENTS_SERVICE_URL = 'http://{}:4567'.format(os.environ['BOK_CHOY_HOSTNAME'])
EDXNOTES_PUBLIC_API = 'http://{}:8042/api/v1'.format(os.environ['BOK_CHOY_HOSTNAME'])

# Docker does not support the syslog socket at /dev/log. Rely on the console.
LOGGING['handlers']['local'] = LOGGING['handlers']['tracking'] = {
    'class': 'logging.NullHandler',
}

LOGGING['loggers']['tracking']['handlers'] = ['console']

# Point the URL used to test YouTube availability to our stub YouTube server
BOK_CHOY_HOST = os.environ['BOK_CHOY_HOSTNAME']
YOUTUBE['API'] = f"http://{BOK_CHOY_HOST}:{YOUTUBE_PORT}/get_youtube_api/"
YOUTUBE['METADATA_URL'] = f"http://{BOK_CHOY_HOST}:{YOUTUBE_PORT}/test_youtube/"
