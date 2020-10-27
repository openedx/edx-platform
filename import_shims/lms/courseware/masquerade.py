from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.masquerade', 'lms.djangoapps.courseware.masquerade')

from lms.djangoapps.courseware.masquerade import *
