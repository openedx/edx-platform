import warnings
warnings.warn("Importing grades.admin instead of lms.djangoapps.grades.admin is deprecated", stacklevel=2)

from lms.djangoapps.grades.admin import *
