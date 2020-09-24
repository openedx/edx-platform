import warnings
warnings.warn("Importing discussion.urls instead of lms.djangoapps.discussion.urls is deprecated", stacklevel=2)

from lms.djangoapps.discussion.urls import *
