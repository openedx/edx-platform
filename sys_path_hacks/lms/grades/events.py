import warnings
warnings.warn("Importing grades.events instead of lms.djangoapps.grades.events is deprecated", stacklevel=2)

from lms.djangoapps.grades.events import *
