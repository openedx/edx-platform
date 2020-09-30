from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.management.commands.recover_account')

from common.djangoapps.student.management.commands.recover_account import *
