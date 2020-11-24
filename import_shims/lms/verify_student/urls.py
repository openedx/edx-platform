from import_shims.warn import warn_deprecated_import

warn_deprecated_import('verify_student.urls', 'lms.djangoapps.verify_student.urls')

from lms.djangoapps.verify_student.urls import *
