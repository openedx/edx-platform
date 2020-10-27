from import_shims.warn import warn_deprecated_import

warn_deprecated_import('support.urls', 'lms.djangoapps.support.urls')

from lms.djangoapps.support.urls import *
