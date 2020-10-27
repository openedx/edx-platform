from import_shims.warn import warn_deprecated_import

warn_deprecated_import('survey.admin', 'lms.djangoapps.survey.admin')

from lms.djangoapps.survey.admin import *
