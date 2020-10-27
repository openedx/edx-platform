from import_shims.warn import warn_deprecated_import

warn_deprecated_import('survey.tests', 'lms.djangoapps.survey.tests')

from lms.djangoapps.survey.tests import *
