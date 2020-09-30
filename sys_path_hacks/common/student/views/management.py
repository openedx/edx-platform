from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.views.management')

from common.djangoapps.student.views.management import *
