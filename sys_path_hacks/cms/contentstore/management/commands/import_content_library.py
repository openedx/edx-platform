from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.management.commands.import_content_library')

from cms.djangoapps.contentstore.management.commands.import_content_library import *
