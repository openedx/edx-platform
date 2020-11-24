from import_shims.warn import warn_deprecated_import

warn_deprecated_import('survey.exceptions', 'lms.djangoapps.survey.exceptions')

from lms.djangoapps.survey.exceptions import *
