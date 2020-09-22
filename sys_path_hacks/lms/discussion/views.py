import warnings
warnings.warn("Importing discussion.views instead of lms.djangoapps.discussion.views is deprecated", stacklevel=2)

from lms.djangoapps.discussion.views import *
