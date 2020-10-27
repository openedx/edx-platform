from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'api.apps')

from cms.djangoapps.api.apps import *
