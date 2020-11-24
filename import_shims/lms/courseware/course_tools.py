from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.course_tools', 'lms.djangoapps.courseware.course_tools')

from lms.djangoapps.courseware.course_tools import *
