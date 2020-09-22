import warnings
warnings.warn("Importing instructor instead of lms.djangoapps.instructor is deprecated", stacklevel=2)

from lms.djangoapps.instructor import *
