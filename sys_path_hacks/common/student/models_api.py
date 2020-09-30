from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.models_api')

from common.djangoapps.student.models_api import *
