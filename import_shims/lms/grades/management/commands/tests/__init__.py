from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.management.commands.tests', 'lms.djangoapps.grades.management.commands.tests')

from lms.djangoapps.grades.management.commands.tests import *
