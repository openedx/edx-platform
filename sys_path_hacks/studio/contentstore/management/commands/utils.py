from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.management.commands.utils')

from cms.djangoapps.contentstore.management.commands.utils import *
