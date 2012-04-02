from common import *

EMAIL_BACKEND = 'django_ses.SESBackend'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

CSRF_COOKIE_DOMAIN = '.mitx.mit.edu'
LIB_URL = 'https://mitxstatic.s3.amazonaws.com/js/'
BOOK_URL = 'https://mitxstatic.s3.amazonaws.com/book_images/'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    }
}

DEBUG = False
TEMPLATE_DEBUG = False
