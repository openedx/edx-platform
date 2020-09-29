from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.management.commands.sync_user_info')

from lms.djangoapps.discussion.management.commands.sync_user_info import *
