import warnings
warnings.warn("Importing grades instead of lms.djangoapps.grades is deprecated", stacklevel=2)

from lms.djangoapps.grades import *
