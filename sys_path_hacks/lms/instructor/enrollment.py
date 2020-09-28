import warnings
warnings.warn("Importing instructor.enrollment instead of lms.djangoapps.instructor.enrollment is deprecated", stacklevel=2)

from lms.djangoapps.instructor.enrollment import *
