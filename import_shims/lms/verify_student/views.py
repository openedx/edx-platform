from import_shims.warn import warn_deprecated_import

warn_deprecated_import('verify_student.views', 'lms.djangoapps.verify_student.views')

from lms.djangoapps.verify_student.views import *
