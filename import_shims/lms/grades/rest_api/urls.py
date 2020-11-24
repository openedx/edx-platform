from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.rest_api.urls', 'lms.djangoapps.grades.rest_api.urls')

from lms.djangoapps.grades.rest_api.urls import *
