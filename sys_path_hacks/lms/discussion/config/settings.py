import warnings
warnings.warn("Importing discussion.config.settings instead of lms.djangoapps.discussion.config.settings is deprecated", stacklevel=2)

from lms.djangoapps.discussion.config.settings import *
