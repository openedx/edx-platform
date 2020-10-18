from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'maintenance.tests')

from cms.djangoapps.maintenance.tests import *
