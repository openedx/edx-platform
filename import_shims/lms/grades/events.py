from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.events', 'lms.djangoapps.grades.events')

from lms.djangoapps.grades.events import *
