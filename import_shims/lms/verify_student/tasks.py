from import_shims.warn import warn_deprecated_import

warn_deprecated_import('verify_student.tasks', 'lms.djangoapps.verify_student.tasks')

from lms.djangoapps.verify_student.tasks import *
