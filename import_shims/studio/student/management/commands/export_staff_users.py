from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.management.commands.export_staff_users', 'common.djangoapps.student.management.commands.export_staff_users')

from common.djangoapps.student.management.commands.export_staff_users import *
