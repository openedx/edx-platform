from import_shims.warn import warn_deprecated_import

warn_deprecated_import('rss_proxy', 'lms.djangoapps.rss_proxy')

from lms.djangoapps.rss_proxy import *
