from import_shims.warn import warn_deprecated_import

warn_deprecated_import('verify_student.signals', 'lms.djangoapps.verify_student.signals')

from lms.djangoapps.verify_student.signals import *
