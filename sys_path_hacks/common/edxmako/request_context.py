from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'edxmako.request_context')

from common.djangoapps.edxmako.request_context import *
