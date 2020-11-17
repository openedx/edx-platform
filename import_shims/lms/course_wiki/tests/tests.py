from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_wiki.tests.tests', 'lms.djangoapps.course_wiki.tests.tests')

from lms.djangoapps.course_wiki.tests.tests import *
