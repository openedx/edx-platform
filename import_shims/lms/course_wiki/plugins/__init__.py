from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_wiki.plugins', 'lms.djangoapps.course_wiki.plugins')

from lms.djangoapps.course_wiki.plugins import *
