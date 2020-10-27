from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.management.commands.reload_forum_users')

from lms.djangoapps.discussion.management.commands.reload_forum_users import *
