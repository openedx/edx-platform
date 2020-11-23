from import_shims.warn import warn_deprecated_import

warn_deprecated_import('survey.views', 'lms.djangoapps.survey.views')

from lms.djangoapps.survey.views import *
