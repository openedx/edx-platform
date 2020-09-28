import warnings
warnings.warn("Importing courseware.user_state_client instead of lms.djangoapps.courseware.user_state_client is deprecated", stacklevel=2)

from lms.djangoapps.courseware.user_state_client import *
