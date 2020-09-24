import warnings
warnings.warn("Importing discussion.management.commands instead of lms.djangoapps.discussion.management.commands is deprecated", stacklevel=2)

from lms.djangoapps.discussion.management.commands import *
