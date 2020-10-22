from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.debug_file_uploader')

from cms.djangoapps.contentstore.debug_file_uploader import *
