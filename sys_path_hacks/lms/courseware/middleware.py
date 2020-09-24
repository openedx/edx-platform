import warnings
warnings.warn("Importing courseware.middleware instead of lms.djangoapps.courseware.middleware is deprecated", stacklevel=2)

from lms.djangoapps.courseware.middleware import *
