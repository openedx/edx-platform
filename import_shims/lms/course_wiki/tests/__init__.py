from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_wiki.tests', 'lms.djangoapps.course_wiki.tests')

from lms.djangoapps.course_wiki.tests import *
