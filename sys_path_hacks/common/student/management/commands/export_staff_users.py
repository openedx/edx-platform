from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.management.commands.export_staff_users')

from common.djangoapps.student.management.commands.export_staff_users import *
