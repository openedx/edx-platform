from import_shims.warn import warn_deprecated_import

warn_deprecated_import('survey.apps', 'lms.djangoapps.survey.apps')

from lms.djangoapps.survey.apps import *
