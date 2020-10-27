from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'gating.apps')

from lms.djangoapps.gating.apps import *
