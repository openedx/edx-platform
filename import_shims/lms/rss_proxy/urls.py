from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'rss_proxy.urls')

from lms.djangoapps.rss_proxy.urls import *
