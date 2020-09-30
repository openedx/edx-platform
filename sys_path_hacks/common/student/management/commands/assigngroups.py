from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.management.commands.assigngroups')

from common.djangoapps.student.management.commands.assigngroups import *
