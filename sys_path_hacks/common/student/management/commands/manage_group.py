from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.management.commands.manage_group')

from common.djangoapps.student.management.commands.manage_group import *
