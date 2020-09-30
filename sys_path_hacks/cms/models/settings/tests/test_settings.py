from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'models.settings.tests.test_settings')

from cms.djangoapps.models.settings.tests.test_settings import *
