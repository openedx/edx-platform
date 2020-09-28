import warnings
warnings.warn("Importing grades.services instead of lms.djangoapps.grades.services is deprecated", stacklevel=2)

from lms.djangoapps.grades.services import *
