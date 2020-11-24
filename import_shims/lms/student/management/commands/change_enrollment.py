from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.management.commands.change_enrollment', 'common.djangoapps.student.management.commands.change_enrollment')

from common.djangoapps.student.management.commands.change_enrollment import *
