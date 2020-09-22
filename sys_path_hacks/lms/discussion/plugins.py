import warnings
warnings.warn("Importing discussion.plugins instead of lms.djangoapps.discussion.plugins is deprecated", stacklevel=2)

from lms.djangoapps.discussion.plugins import *
