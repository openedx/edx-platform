from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.config')

from cms.djangoapps.contentstore.config import *
