from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.management.commands.set_staff')

from common.djangoapps.student.management.commands.set_staff import *
