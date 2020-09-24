import warnings
warnings.warn("Importing grades.config instead of lms.djangoapps.grades.config is deprecated", stacklevel=2)

from lms.djangoapps.grades.config import *
