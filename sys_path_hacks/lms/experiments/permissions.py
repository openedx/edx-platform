from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'experiments.permissions')

from lms.djangoapps.experiments.permissions import *
