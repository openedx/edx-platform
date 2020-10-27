from import_shims.warn import warn_deprecated_import

warn_deprecated_import('verify_student', 'lms.djangoapps.verify_student')

from lms.djangoapps.verify_student import *
