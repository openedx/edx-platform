from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'entitlements.rest_api.v1.permissions')

from common.djangoapps.entitlements.rest_api.v1.permissions import *
