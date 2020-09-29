from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'grades.rest_api.v1.utils')

from lms.djangoapps.grades.rest_api.v1.utils import *
