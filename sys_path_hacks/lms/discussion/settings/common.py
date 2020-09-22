import warnings
warnings.warn("Importing discussion.settings.common instead of lms.djangoapps.discussion.settings.common is deprecated", stacklevel=2)

from lms.djangoapps.discussion.settings.common import *
