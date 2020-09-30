from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.management.commands.create_random_users')

from common.djangoapps.student.management.commands.create_random_users import *
