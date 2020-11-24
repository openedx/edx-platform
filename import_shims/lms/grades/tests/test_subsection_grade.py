from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.tests.test_subsection_grade', 'lms.djangoapps.grades.tests.test_subsection_grade')

from lms.djangoapps.grades.tests.test_subsection_grade import *
