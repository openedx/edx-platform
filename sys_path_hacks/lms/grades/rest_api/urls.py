from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'grades.rest_api.urls')

from lms.djangoapps.grades.rest_api.urls import *
