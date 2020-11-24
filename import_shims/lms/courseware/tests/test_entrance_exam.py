from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tests.test_entrance_exam', 'lms.djangoapps.courseware.tests.test_entrance_exam')

from lms.djangoapps.courseware.tests.test_entrance_exam import *
