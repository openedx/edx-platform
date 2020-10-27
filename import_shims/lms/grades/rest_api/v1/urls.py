from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.rest_api.v1.urls', 'lms.djangoapps.grades.rest_api.v1.urls')

from lms.djangoapps.grades.rest_api.v1.urls import *
