import warnings
warnings.warn("Importing grades.config.models instead of lms.djangoapps.grades.config.models is deprecated", stacklevel=2)

from lms.djangoapps.grades.config.models import *
