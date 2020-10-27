from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'experiments.utils')

from lms.djangoapps.experiments.utils import *
