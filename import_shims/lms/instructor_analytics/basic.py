from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor_analytics.basic')

from lms.djangoapps.instructor_analytics.basic import *
