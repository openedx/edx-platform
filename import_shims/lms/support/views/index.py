from import_shims.warn import warn_deprecated_import

warn_deprecated_import('support.views.index', 'lms.djangoapps.support.views.index')

from lms.djangoapps.support.views.index import *
