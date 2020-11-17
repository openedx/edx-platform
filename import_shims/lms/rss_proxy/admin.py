from import_shims.warn import warn_deprecated_import

warn_deprecated_import('rss_proxy.admin', 'lms.djangoapps.rss_proxy.admin')

from lms.djangoapps.rss_proxy.admin import *
