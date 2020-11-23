from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.rest_api', 'lms.djangoapps.grades.rest_api')

from lms.djangoapps.grades.rest_api import *
