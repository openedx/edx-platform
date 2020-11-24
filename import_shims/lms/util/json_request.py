from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.json_request', 'common.djangoapps.util.json_request')

from common.djangoapps.util.json_request import *
