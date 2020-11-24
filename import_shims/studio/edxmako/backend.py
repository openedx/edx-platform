from import_shims.warn import warn_deprecated_import

warn_deprecated_import('edxmako.backend', 'common.djangoapps.edxmako.backend')

from common.djangoapps.edxmako.backend import *
