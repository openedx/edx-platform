from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.management.commands.change_eligibility_deadline')

from common.djangoapps.student.management.commands.change_eligibility_deadline import *
