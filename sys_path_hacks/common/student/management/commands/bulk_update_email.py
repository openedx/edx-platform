from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.management.commands.bulk_update_email')

from common.djangoapps.student.management.commands.bulk_update_email import *
