import warnings
warnings.warn("Importing discussion.rest_api.urls instead of lms.djangoapps.discussion.rest_api.urls is deprecated", stacklevel=2)

from lms.djangoapps.discussion.rest_api.urls import *
