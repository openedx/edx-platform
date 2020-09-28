import warnings
warnings.warn("Importing courseware.services instead of lms.djangoapps.courseware.services is deprecated", stacklevel=2)

from lms.djangoapps.courseware.services import *
