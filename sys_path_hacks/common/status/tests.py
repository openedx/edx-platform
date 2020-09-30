from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'status.tests')

from common.djangoapps.status.tests import *
