from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'experiments.admin')

from lms.djangoapps.experiments.admin import *
