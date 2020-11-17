from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.management.commands', 'lms.djangoapps.courseware.management.commands')

from lms.djangoapps.courseware.management.commands import *
