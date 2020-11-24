from import_shims.warn import warn_deprecated_import

warn_deprecated_import('verify_student.ssencrypt', 'lms.djangoapps.verify_student.ssencrypt')

from lms.djangoapps.verify_student.ssencrypt import *
