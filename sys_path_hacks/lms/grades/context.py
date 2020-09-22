import warnings
warnings.warn("Importing grades.context instead of lms.djangoapps.grades.context is deprecated", stacklevel=2)

from lms.djangoapps.grades.context import *
