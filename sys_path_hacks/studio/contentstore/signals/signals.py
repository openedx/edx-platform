from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.signals.signals')

from cms.djangoapps.contentstore.signals.signals import *
