from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'edxmako.makoloader')

from common.djangoapps.edxmako.makoloader import *
