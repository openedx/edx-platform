from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.management.commands.change_enterprise_user_username')

from common.djangoapps.student.management.commands.change_enterprise_user_username import *
