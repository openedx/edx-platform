from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'edxmako.template')

from common.djangoapps.edxmako.template import *
