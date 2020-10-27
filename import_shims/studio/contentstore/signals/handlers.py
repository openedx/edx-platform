from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.signals.handlers')

from cms.djangoapps.contentstore.signals.handlers import *
