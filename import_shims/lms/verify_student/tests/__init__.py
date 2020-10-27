from import_shims.warn import warn_deprecated_import

warn_deprecated_import('verify_student.tests', 'lms.djangoapps.verify_student.tests')

from lms.djangoapps.verify_student.tests import *
