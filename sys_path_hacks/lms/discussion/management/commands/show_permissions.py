import warnings
warnings.warn("Importing discussion.management.commands.show_permissions instead of lms.djangoapps.discussion.management.commands.show_permissions is deprecated", stacklevel=2)

from lms.djangoapps.discussion.management.commands.show_permissions import *
