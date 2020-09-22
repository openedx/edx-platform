import warnings
warnings.warn("Importing courseware.courses instead of lms.djangoapps.courseware.courses is deprecated", stacklevel=2)

from lms.djangoapps.courseware.courses import *
