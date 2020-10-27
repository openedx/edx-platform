from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.config.forms', 'lms.djangoapps.grades.config.forms')

from lms.djangoapps.grades.config.forms import *
