from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_wiki.editors', 'lms.djangoapps.course_wiki.editors')

from lms.djangoapps.course_wiki.editors import *
