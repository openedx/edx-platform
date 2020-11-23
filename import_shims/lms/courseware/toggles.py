from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.toggles', 'lms.djangoapps.courseware.toggles')

from lms.djangoapps.courseware.toggles import *
