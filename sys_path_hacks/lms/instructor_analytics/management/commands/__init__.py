from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor_analytics.management.commands')

from lms.djangoapps.instructor_analytics.management.commands import *
