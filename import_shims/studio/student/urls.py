from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.urls', 'common.djangoapps.student.urls')

from common.djangoapps.student.urls import *
