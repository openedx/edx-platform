import warnings
warnings.warn("Importing grades.settings instead of lms.djangoapps.grades.settings is deprecated", stacklevel=2)

from lms.djangoapps.grades.settings import *
