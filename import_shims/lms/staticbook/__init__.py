from import_shims.warn import warn_deprecated_import

warn_deprecated_import('staticbook', 'lms.djangoapps.staticbook')

from lms.djangoapps.staticbook import *
