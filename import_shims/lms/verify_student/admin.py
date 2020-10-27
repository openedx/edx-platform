from import_shims.warn import warn_deprecated_import

warn_deprecated_import('verify_student.admin', 'lms.djangoapps.verify_student.admin')

from lms.djangoapps.verify_student.admin import *
