from import_shims.warn import warn_deprecated_import

warn_deprecated_import('dashboard.sysadmin_urls', 'lms.djangoapps.dashboard.sysadmin_urls')

from lms.djangoapps.dashboard.sysadmin_urls import *
