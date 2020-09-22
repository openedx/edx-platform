import warnings
warnings.warn("Importing grades.models instead of lms.djangoapps.grades.models is deprecated", stacklevel=2)

from lms.djangoapps.grades.models import *
