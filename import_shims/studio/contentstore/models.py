from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.models')

from cms.djangoapps.contentstore.models import *
