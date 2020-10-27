from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.management.commands.tests.test_compute_grades', 'lms.djangoapps.grades.management.commands.tests.test_compute_grades')

from lms.djangoapps.grades.management.commands.tests.test_compute_grades import *
