from import_shims.warn import warn_deprecated_import

warn_deprecated_import('survey.urls', 'lms.djangoapps.survey.urls')

from lms.djangoapps.survey.urls import *
