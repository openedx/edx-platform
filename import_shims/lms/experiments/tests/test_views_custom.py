from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'experiments.tests.test_views_custom')

from lms.djangoapps.experiments.tests.test_views_custom import *
