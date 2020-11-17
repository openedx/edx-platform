from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_wiki.tests.test_access', 'lms.djangoapps.course_wiki.tests.test_access')

from lms.djangoapps.course_wiki.tests.test_access import *
