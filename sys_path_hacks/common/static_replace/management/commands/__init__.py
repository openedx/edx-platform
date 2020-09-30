from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'static_replace.management.commands')

from common.djangoapps.static_replace.management.commands import *
