from import_shims.warn import warn_deprecated_import

warn_deprecated_import('survey.tests.test_signals', 'lms.djangoapps.survey.tests.test_signals')

from lms.djangoapps.survey.tests.test_signals import *
