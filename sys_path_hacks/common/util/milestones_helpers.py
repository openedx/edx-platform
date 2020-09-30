from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'util.milestones_helpers')

from common.djangoapps.util.milestones_helpers import *
