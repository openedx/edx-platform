from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.roles', 'common.djangoapps.student.roles')

from common.djangoapps.student.roles import *
