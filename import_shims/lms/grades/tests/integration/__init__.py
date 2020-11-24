from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.tests.integration', 'lms.djangoapps.grades.tests.integration')

from lms.djangoapps.grades.tests.integration import *
