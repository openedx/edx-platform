import warnings
warnings.warn("Importing grades.api instead of lms.djangoapps.grades.api is deprecated", stacklevel=2)

from lms.djangoapps.grades.api import *
