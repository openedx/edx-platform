from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'util.keyword_substitution')

from common.djangoapps.util.keyword_substitution import *
