from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'experiments.apps')

from lms.djangoapps.experiments.apps import *
