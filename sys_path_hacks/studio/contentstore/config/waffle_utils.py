from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.config.waffle_utils')

from cms.djangoapps.contentstore.config.waffle_utils import *
