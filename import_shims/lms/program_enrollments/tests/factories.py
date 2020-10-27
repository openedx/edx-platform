from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'program_enrollments.tests.factories')

from lms.djangoapps.program_enrollments.tests.factories import *
