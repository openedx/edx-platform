from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.views.preview')

from cms.djangoapps.contentstore.views.preview import *
