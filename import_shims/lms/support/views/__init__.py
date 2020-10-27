from import_shims.warn import warn_deprecated_import

warn_deprecated_import('support.views', 'lms.djangoapps.support.views')

from lms.djangoapps.support.views import *
