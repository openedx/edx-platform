from import_shims.warn import warn_deprecated_import

warn_deprecated_import('survey.tests.test_models', 'lms.djangoapps.survey.tests.test_models')

from lms.djangoapps.survey.tests.test_models import *
