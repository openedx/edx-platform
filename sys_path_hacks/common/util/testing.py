from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'util.testing')

from common.djangoapps.util.testing import *
