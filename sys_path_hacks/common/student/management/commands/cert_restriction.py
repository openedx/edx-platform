from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.management.commands.cert_restriction')

from common.djangoapps.student.management.commands.cert_restriction import *
