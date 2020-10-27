from import_shims.warn import warn_deprecated_import

warn_deprecated_import('verify_student.api', 'lms.djangoapps.verify_student.api')

from lms.djangoapps.verify_student.api import *
