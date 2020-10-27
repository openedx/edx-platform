from import_shims.warn import warn_deprecated_import

warn_deprecated_import('verify_student.management', 'lms.djangoapps.verify_student.management')

from lms.djangoapps.verify_student.management import *
