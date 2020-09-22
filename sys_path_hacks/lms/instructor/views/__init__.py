import warnings
warnings.warn("Importing instructor.views instead of lms.djangoapps.instructor.views is deprecated", stacklevel=2)

from lms.djangoapps.instructor.views import *
