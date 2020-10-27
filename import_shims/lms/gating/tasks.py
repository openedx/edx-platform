from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'gating.tasks')

from lms.djangoapps.gating.tasks import *
