from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.management.commands.get_discussion_link')

from lms.djangoapps.discussion.management.commands.get_discussion_link import *
