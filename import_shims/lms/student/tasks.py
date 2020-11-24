from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.tasks', 'common.djangoapps.student.tasks')

from common.djangoapps.student.tasks import *
