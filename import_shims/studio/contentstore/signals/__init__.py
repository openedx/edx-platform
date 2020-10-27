from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.signals', 'cms.djangoapps.contentstore.signals')

from cms.djangoapps.contentstore.signals import *
