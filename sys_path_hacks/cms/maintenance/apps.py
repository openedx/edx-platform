from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'maintenance.apps')

from cms.djangoapps.maintenance.apps import *
