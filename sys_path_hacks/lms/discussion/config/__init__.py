import warnings
warnings.warn("Importing discussion.config instead of lms.djangoapps.discussion.config is deprecated", stacklevel=2)

from lms.djangoapps.discussion.config import *
