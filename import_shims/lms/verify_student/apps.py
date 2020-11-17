from import_shims.warn import warn_deprecated_import

warn_deprecated_import('verify_student.apps', 'lms.djangoapps.verify_student.apps')

from lms.djangoapps.verify_student.apps import *
