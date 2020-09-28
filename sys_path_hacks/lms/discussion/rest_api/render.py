import warnings
warnings.warn("Importing discussion.rest_api.render instead of lms.djangoapps.discussion.rest_api.render is deprecated", stacklevel=2)

from lms.djangoapps.discussion.rest_api.render import *
