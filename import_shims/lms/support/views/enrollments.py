from import_shims.warn import warn_deprecated_import

warn_deprecated_import('support.views.enrollments', 'lms.djangoapps.support.views.enrollments')

from lms.djangoapps.support.views.enrollments import *
