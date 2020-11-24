from import_shims.warn import warn_deprecated_import

warn_deprecated_import('survey', 'lms.djangoapps.survey')

from lms.djangoapps.survey import *
