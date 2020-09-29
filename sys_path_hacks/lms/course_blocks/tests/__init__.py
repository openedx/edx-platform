from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'course_blocks.tests')

from lms.djangoapps.course_blocks.tests import *
