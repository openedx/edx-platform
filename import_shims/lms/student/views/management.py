from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.views.management', 'common.djangoapps.student.views.management')

from common.djangoapps.student.views.management import *
