from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'edxmako.shortcuts')

from common.djangoapps.edxmako.shortcuts import *
