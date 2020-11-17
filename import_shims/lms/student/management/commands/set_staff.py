from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.management.commands.set_staff', 'common.djangoapps.student.management.commands.set_staff')

from common.djangoapps.student.management.commands.set_staff import *
