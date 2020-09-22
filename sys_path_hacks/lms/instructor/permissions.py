import warnings
warnings.warn("Importing instructor.permissions instead of lms.djangoapps.instructor.permissions is deprecated", stacklevel=2)

from lms.djangoapps.instructor.permissions import *
