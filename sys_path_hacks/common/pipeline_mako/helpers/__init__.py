from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'pipeline_mako.helpers')

from common.djangoapps.pipeline_mako.helpers import *
