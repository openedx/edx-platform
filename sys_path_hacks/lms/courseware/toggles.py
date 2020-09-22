import warnings
warnings.warn("Importing courseware.toggles instead of lms.djangoapps.courseware.toggles is deprecated", stacklevel=2)

from lms.djangoapps.courseware.toggles import *
