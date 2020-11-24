from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.management.commands', 'common.djangoapps.student.management.commands')

from common.djangoapps.student.management.commands import *
