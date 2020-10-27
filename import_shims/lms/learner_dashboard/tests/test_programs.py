from import_shims.warn import warn_deprecated_import

warn_deprecated_import('learner_dashboard.tests.test_programs', 'lms.djangoapps.learner_dashboard.tests.test_programs')

from lms.djangoapps.learner_dashboard.tests.test_programs import *
