from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'learner_dashboard.tests')

from lms.djangoapps.learner_dashboard.tests import *
