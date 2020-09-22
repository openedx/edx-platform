import warnings
warnings.warn("Importing discussion.settings instead of lms.djangoapps.discussion.settings is deprecated", stacklevel=2)

from lms.djangoapps.discussion.settings import *
