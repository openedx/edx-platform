from import_shims.warn import warn_deprecated_import

warn_deprecated_import('verify_student.models', 'lms.djangoapps.verify_student.models')

from lms.djangoapps.verify_student.models import *
