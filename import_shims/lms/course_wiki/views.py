from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_wiki.views', 'lms.djangoapps.course_wiki.views')

from lms.djangoapps.course_wiki.views import *
