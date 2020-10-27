from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_wiki.tests.test_tab', 'lms.djangoapps.course_wiki.tests.test_tab')

from lms.djangoapps.course_wiki.tests.test_tab import *
