from import_shims.warn import warn_deprecated_import

warn_deprecated_import('verify_student.management.commands', 'lms.djangoapps.verify_student.management.commands')

from lms.djangoapps.verify_student.management.commands import *
