from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'course_goals.models')

from lms.djangoapps.course_goals.models import *
