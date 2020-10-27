from import_shims.warn import warn_deprecated_import

warn_deprecated_import('verify_student.services', 'lms.djangoapps.verify_student.services')

from lms.djangoapps.verify_student.services import *
