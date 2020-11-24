from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.settings.production', 'lms.djangoapps.grades.settings.production')

from lms.djangoapps.grades.settings.production import *
