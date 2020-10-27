from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_blocks.tests', 'lms.djangoapps.course_blocks.tests')

from lms.djangoapps.course_blocks.tests import *
