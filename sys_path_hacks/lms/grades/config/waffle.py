import warnings
warnings.warn("Importing grades.config.waffle instead of lms.djangoapps.grades.config.waffle is deprecated", stacklevel=2)

from lms.djangoapps.grades.config.waffle import *
