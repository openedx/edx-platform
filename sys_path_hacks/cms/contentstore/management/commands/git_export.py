from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.management.commands.git_export')

from cms.djangoapps.contentstore.management.commands.git_export import *
