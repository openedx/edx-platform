from import_shims.warn import warn_deprecated_import

warn_deprecated_import('rss_proxy.views', 'lms.djangoapps.rss_proxy.views')

from lms.djangoapps.rss_proxy.views import *
