from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.settings.common', 'lms.djangoapps.grades.settings.common')

from lms.djangoapps.grades.settings.common import *
