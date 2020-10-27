from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.management', 'cms.djangoapps.contentstore.management')

from cms.djangoapps.contentstore.management import *
