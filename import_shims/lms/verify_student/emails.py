from import_shims.warn import warn_deprecated_import

warn_deprecated_import('verify_student.emails', 'lms.djangoapps.verify_student.emails')

from lms.djangoapps.verify_student.emails import *
