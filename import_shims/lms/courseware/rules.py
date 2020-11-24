from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.rules', 'lms.djangoapps.courseware.rules')

from lms.djangoapps.courseware.rules import *
