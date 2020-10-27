from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor_analytics.management')

from lms.djangoapps.instructor_analytics.management import *
