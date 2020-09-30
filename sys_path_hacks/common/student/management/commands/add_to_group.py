from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.management.commands.add_to_group')

from common.djangoapps.student.management.commands.add_to_group import *
