from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.config.waffle', 'lms.djangoapps.grades.config.waffle')

from lms.djangoapps.grades.config.waffle import *
