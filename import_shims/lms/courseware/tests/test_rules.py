from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tests.test_rules', 'lms.djangoapps.courseware.tests.test_rules')

from lms.djangoapps.courseware.tests.test_rules import *
