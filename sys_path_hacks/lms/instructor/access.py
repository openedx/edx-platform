import warnings
warnings.warn("Importing instructor.access instead of lms.djangoapps.instructor.access is deprecated", stacklevel=2)

from lms.djangoapps.instructor.access import *
