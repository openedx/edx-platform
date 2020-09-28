import warnings
warnings.warn("Importing discussion.management.commands.get_discussion_link instead of lms.djangoapps.discussion.management.commands.get_discussion_link is deprecated", stacklevel=2)

from lms.djangoapps.discussion.management.commands.get_discussion_link import *
