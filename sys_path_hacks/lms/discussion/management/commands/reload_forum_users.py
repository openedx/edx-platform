import warnings
warnings.warn("Importing discussion.management.commands.reload_forum_users instead of lms.djangoapps.discussion.management.commands.reload_forum_users is deprecated", stacklevel=2)

from lms.djangoapps.discussion.management.commands.reload_forum_users import *
