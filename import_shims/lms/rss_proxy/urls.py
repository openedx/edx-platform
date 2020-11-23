from import_shims.warn import warn_deprecated_import

warn_deprecated_import('rss_proxy.urls', 'lms.djangoapps.rss_proxy.urls')

from lms.djangoapps.rss_proxy.urls import *
