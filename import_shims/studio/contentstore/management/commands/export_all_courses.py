from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.management.commands.export_all_courses', 'cms.djangoapps.contentstore.management.commands.export_all_courses')

from cms.djangoapps.contentstore.management.commands.export_all_courses import *
