from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'static_replace.test')

from common.djangoapps.static_replace.test import *
