from import_shims.warn import warn_deprecated_import

warn_deprecated_import('survey.models', 'lms.djangoapps.survey.models')

from lms.djangoapps.survey.models import *
