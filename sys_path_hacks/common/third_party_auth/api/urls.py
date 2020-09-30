from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'third_party_auth.api.urls')

from common.djangoapps.third_party_auth.api.urls import *
