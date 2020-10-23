from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'models.settings.encoder')

from cms.djangoapps.models.settings.encoder import *
