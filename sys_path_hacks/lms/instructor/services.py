import warnings
warnings.warn("Importing instructor.services instead of lms.djangoapps.instructor.services is deprecated", stacklevel=2)

from lms.djangoapps.instructor.services import *
