from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_wiki.tab', 'lms.djangoapps.course_wiki.tab')

from lms.djangoapps.course_wiki.tab import *
