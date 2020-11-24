from import_shims.warn import warn_deprecated_import

warn_deprecated_import('edxmako.apps', 'common.djangoapps.edxmako.apps')

from common.djangoapps.edxmako.apps import *
