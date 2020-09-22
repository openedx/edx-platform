import warnings
warnings.warn("Importing grades.config.forms instead of lms.djangoapps.grades.config.forms is deprecated", stacklevel=2)

from lms.djangoapps.grades.config.forms import *
