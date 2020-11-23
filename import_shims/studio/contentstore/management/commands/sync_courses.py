from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.management.commands.sync_courses', 'cms.djangoapps.contentstore.management.commands.sync_courses')

from cms.djangoapps.contentstore.management.commands.sync_courses import *
