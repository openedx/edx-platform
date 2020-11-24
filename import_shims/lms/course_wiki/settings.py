from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_wiki.settings', 'lms.djangoapps.course_wiki.settings')

from lms.djangoapps.course_wiki.settings import *
