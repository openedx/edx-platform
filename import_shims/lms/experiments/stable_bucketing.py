from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'experiments.stable_bucketing')

from lms.djangoapps.experiments.stable_bucketing import *
