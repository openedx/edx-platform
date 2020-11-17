from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.management', 'lms.djangoapps.courseware.management')

from lms.djangoapps.courseware.management import *
