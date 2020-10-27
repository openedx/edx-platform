from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'experiments.views_custom')

from lms.djangoapps.experiments.views_custom import *
