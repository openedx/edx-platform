from import_shims.warn import warn_deprecated_import

warn_deprecated_import('survey.signals', 'lms.djangoapps.survey.signals')

from lms.djangoapps.survey.signals import *
