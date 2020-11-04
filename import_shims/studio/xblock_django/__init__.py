from import_shims.warn import warn_deprecated_import

warn_deprecated_import('xblock_django', 'common.djangoapps.xblock_django')

from common.djangoapps.xblock_django import *
