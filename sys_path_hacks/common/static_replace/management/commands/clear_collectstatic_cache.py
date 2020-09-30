from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'static_replace.management.commands.clear_collectstatic_cache')

from common.djangoapps.static_replace.management.commands.clear_collectstatic_cache import *
