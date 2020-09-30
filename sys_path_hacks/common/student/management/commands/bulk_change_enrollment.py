from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.management.commands.bulk_change_enrollment')

from common.djangoapps.student.management.commands.bulk_change_enrollment import *
