from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.settings.test', 'lms.djangoapps.grades.settings.test')

from lms.djangoapps.grades.settings.test import *
