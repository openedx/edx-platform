from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.management', 'common.djangoapps.student.management')

from common.djangoapps.student.management import *
