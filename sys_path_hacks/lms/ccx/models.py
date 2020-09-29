from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'ccx.models')

from lms.djangoapps.ccx.models import *
