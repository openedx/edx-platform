from import_shims.warn import warn_deprecated_import

warn_deprecated_import('verify_student.management.commands.tests', 'lms.djangoapps.verify_student.management.commands.tests')

from lms.djangoapps.verify_student.management.commands.tests import *
