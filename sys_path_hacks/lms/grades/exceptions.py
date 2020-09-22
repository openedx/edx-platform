import warnings
warnings.warn("Importing grades.exceptions instead of lms.djangoapps.grades.exceptions is deprecated", stacklevel=2)

from lms.djangoapps.grades.exceptions import *
