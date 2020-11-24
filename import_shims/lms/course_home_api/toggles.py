from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_home_api.toggles', 'lms.djangoapps.course_home_api.toggles')

from lms.djangoapps.course_home_api.toggles import *
