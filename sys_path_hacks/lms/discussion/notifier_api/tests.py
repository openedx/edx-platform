from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.notifier_api.tests')

from lms.djangoapps.discussion.notifier_api.tests import *
