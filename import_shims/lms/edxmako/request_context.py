from import_shims.warn import warn_deprecated_import

warn_deprecated_import('edxmako.request_context', 'common.djangoapps.edxmako.request_context')

from common.djangoapps.edxmako.request_context import *
