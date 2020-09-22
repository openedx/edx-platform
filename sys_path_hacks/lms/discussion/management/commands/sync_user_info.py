import warnings
warnings.warn("Importing discussion.management.commands.sync_user_info instead of lms.djangoapps.discussion.management.commands.sync_user_info is deprecated", stacklevel=2)

from lms.djangoapps.discussion.management.commands.sync_user_info import *
