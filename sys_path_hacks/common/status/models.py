from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'status.models')

from common.djangoapps.status.models import *
