from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'grades.rest_api.v1.gradebook_views')

from lms.djangoapps.grades.rest_api.v1.gradebook_views import *
