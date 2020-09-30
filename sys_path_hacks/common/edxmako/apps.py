from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'edxmako.apps')

from common.djangoapps.edxmako.apps import *
