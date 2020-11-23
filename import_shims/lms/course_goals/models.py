from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_goals.models', 'lms.djangoapps.course_goals.models')

from lms.djangoapps.course_goals.models import *
