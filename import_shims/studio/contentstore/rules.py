from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.rules', 'cms.djangoapps.contentstore.rules')

from cms.djangoapps.contentstore.rules import *
