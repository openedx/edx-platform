from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'util.tests.test_json_request')

from common.djangoapps.util.tests.test_json_request import *
