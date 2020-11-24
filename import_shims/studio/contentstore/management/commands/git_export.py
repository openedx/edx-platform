from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.management.commands.git_export', 'cms.djangoapps.contentstore.management.commands.git_export')

from cms.djangoapps.contentstore.management.commands.git_export import *
