from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.apps')

from cms.djangoapps.contentstore.apps import *
