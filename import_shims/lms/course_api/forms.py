from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_api.forms', 'lms.djangoapps.course_api.forms')

from lms.djangoapps.course_api.forms import *
