from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'pipeline_mako.tests.test_static_content')

from common.djangoapps.pipeline_mako.tests.test_static_content import *
