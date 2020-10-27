from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.views.error')

from cms.djangoapps.contentstore.views.error import *
