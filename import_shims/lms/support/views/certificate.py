from import_shims.warn import warn_deprecated_import

warn_deprecated_import('support.views.certificate', 'lms.djangoapps.support.views.certificate')

from lms.djangoapps.support.views.certificate import *
