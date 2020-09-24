import warnings
warnings.warn("Importing instructor.settings instead of lms.djangoapps.instructor.settings is deprecated", stacklevel=2)

from lms.djangoapps.instructor.settings import *
