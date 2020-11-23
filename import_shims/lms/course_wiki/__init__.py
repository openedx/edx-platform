from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_wiki', 'lms.djangoapps.course_wiki')

from lms.djangoapps.course_wiki import *
