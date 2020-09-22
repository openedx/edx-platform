import warnings
warnings.warn("Importing discussion.rest_api.api instead of lms.djangoapps.discussion.rest_api.api is deprecated", stacklevel=2)

from lms.djangoapps.discussion.rest_api.api import *
