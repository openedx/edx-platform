from import_shims.warn import warn_deprecated_import

warn_deprecated_import('staticbook.views', 'lms.djangoapps.staticbook.views')

from lms.djangoapps.staticbook.views import *
