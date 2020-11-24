from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.rest_api.v1', 'lms.djangoapps.grades.rest_api.v1')

from lms.djangoapps.grades.rest_api.v1 import *
