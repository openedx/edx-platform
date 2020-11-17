from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.management.commands', 'cms.djangoapps.contentstore.management.commands')

from cms.djangoapps.contentstore.management.commands import *
