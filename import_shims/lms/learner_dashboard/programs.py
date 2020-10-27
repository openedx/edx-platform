from import_shims.warn import warn_deprecated_import

warn_deprecated_import('learner_dashboard.programs', 'lms.djangoapps.learner_dashboard.programs')

from lms.djangoapps.learner_dashboard.programs import *
