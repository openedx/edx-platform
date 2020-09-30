from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'status.status')

from common.djangoapps.status.status import *
